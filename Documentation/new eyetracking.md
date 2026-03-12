# Eye Tracking Development (as of 12/03/2026)

## Previous work
Our group previously tried creating an eyetracking program written in Python that would connect to OpenHab and Velbus. However, this solution was ineffective, as its functionality was limited on a raspberry pi -- namely, difficulties with consistently detecting eye movement and connecting to OpenHAB and Velbus. This lead to our team trying a solution based on javascript that connects to Node-RED, which is currently a work in progress. 

## Technology

The eyetracking is handled using webgazer.js, an open-source, javascript-based, eye tracking library. Webgazer is desigined to be used with a webcam, which allows our proof of concept and Minimal Viable Product (MVP) to be used with the equipment we have available. This is used with an HTML front-end, and the signals recieved are passed along to a node-RED program which is connected to velbus. Other solutions, such as OpenHab, were tested, and we found that node-RED was able to connect to Velbus most effectively . This has the advantage of being able to be run locally, with no video data being sent to an external server. 

## Known Limitations and areas for improvement
* Currently, the front-end for the eye-tracker requires a user to calibrate it by clicking on the screen while looking at their cursor, ideally several times. According to WebAIM (2012), mouse-only controls can be inaccessible to those with motor disabilites.
* While the eye-tracking is good enough for someone to activate a lightbulb, it is not fully accurate, and we found during testing that it is less accurate with people who wear glasses to the point of unusability.
* Currently the front-end only has one panel, one that activates a light-bulb. We plan to implement more zones based on feedback.
* As of now, the eyetracking front-end runs on a seperate computer, and is yet to be tested on the raspberry pi.
