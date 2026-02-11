import json
import time
import logging

log = logging.getLogger(__name__)

# gemini is optional
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    log.info("google-genai not installed, AI features disabled")


# the tools gemini can call - these map to openhab actions
TOOL_DECLARATIONS = [
    {
        "name": "turn_on",
        "description": "Turn on a device",
        "parameters": {
            "type": "object",
            "properties": {
                "item_name": {"type": "string", "description": "openhab item name"}
            },
            "required": ["item_name"],
        },
    },
    {
        "name": "turn_off",
        "description": "Turn off a device",
        "parameters": {
            "type": "object",
            "properties": {
                "item_name": {"type": "string", "description": "openhab item name"}
            },
            "required": ["item_name"],
        },
    },
    {
        "name": "toggle",
        "description": "Toggle a device on/off",
        "parameters": {
            "type": "object",
            "properties": {
                "item_name": {"type": "string", "description": "openhab item name"}
            },
            "required": ["item_name"],
        },
    },
    {
        "name": "set_brightness",
        "description": "Set brightness level of a light",
        "parameters": {
            "type": "object",
            "properties": {
                "item_name": {"type": "string", "description": "openhab item name"},
                "level": {"type": "integer", "description": "brightness 0-100"},
            },
            "required": ["item_name", "level"],
        },
    },
    {
        "name": "set_position",
        "description": "Set position of blinds or shutters",
        "parameters": {
            "type": "object",
            "properties": {
                "item_name": {"type": "string", "description": "openhab item name"},
                "position": {"type": "string", "description": "UP, DOWN, or STOP"},
            },
            "required": ["item_name", "position"],
        },
    },
]

SYSTEM_PROMPT = """You are an assistant for a home automation system used by a child who cannot speak or use their hands.
They control things by looking at zones on a screen.

When a routine zone is triggered, decide which devices to control based on:
- The routine name (e.g. "Bedtime" means wind down for sleep)
- The current time of day
- The current device states

Return the appropriate function calls. Keep it simple - just do what makes sense.
Also return a short friendly log message describing what you did."""


class AIAssistant:
    """
    background AI that handles routines and smart logging.
    only called when something actually happens, not every frame.
    """

    def __init__(self, api_key=None, model="gemini-2.0-flash"):
        self.enabled = False
        self.client = None
        self.model = model

        if not GEMINI_AVAILABLE:
            log.info("gemini not available, AI assistant disabled")
            return

        if not api_key or api_key == "YOUR_KEY_HERE":
            log.info("no gemini API key, AI assistant disabled")
            return

        try:
            self.client = genai.Client(api_key=api_key)
            self.enabled = True
            log.info("AI assistant ready")
        except Exception as e:
            log.error(f"failed to init gemini: {e}")

    def handle_routine(self, zone_name, device_states=None, current_time=None):
        """
        called when user triggers a routine zone (like "Bedtime").
        asks gemini what actions to take and returns them.
        """
        if not self.enabled:
            return self._default_routine(zone_name)

        if current_time is None:
            current_time = time.strftime("%H:%M")

        prompt = (
            f"The user triggered the '{zone_name}' routine.\n"
            f"Current time: {current_time}\n"
            f"Device states: {json.dumps(device_states or {})}\n"
            f"What should happen? Use the available functions."
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=[types.Tool(
                        function_declarations=[
                            types.FunctionDeclaration(**t) for t in TOOL_DECLARATIONS
                        ]
                    )],
                ),
            )

            return self._parse_response(response)

        except Exception as e:
            log.error(f"gemini request failed: {e}")
            return self._default_routine(zone_name)

    def generate_log_message(self, zone_name, action, item_name=None):
        """generate a nice log message for mqtt/caregivers"""
        if not self.enabled:
            return f"{zone_name}: {action}"

        try:
            prompt = (
                f"Write a short, friendly log message (one line) for a caregiver. "
                f"The child just triggered: zone='{zone_name}', "
                f"action='{action}', device='{item_name or 'N/A'}'. "
                f"Time: {time.strftime('%H:%M')}. Keep it under 15 words."
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text.strip()

        except Exception:
            return f"{zone_name}: {action}"

    def _parse_response(self, response):
        """pull out function calls from gemini's response"""
        actions = []
        log_message = ""

        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.function_call:
                    fc = part.function_call
                    actions.append({
                        "function": fc.name,
                        "args": dict(fc.args) if fc.args else {},
                    })
                elif part.text:
                    log_message = part.text.strip()

        return {
            "actions": actions,
            "log_message": log_message or f"routine completed ({len(actions)} actions)",
        }

    def _default_routine(self, zone_name):
        """fallback when gemini isn't available"""
        # basic hardcoded routines
        if "bedtime" in zone_name.lower():
            return {
                "actions": [
                    {"function": "turn_off", "args": {"item_name": "LivingRoom_Light"}},
                    {"function": "set_position", "args": {"item_name": "Bedroom_Blinds", "position": "DOWN"}},
                ],
                "log_message": "bedtime routine: lights off, blinds down",
            }

        return {
            "actions": [],
            "log_message": f"no default routine for '{zone_name}'",
        }
