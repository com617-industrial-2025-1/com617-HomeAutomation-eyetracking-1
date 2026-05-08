<!-- Cover Sheet -->
# COM617 Project Initiation Document (PID)

### Project name: Home Automation -- Eyetracking
### Group Members: [insert names here]
### Supporting tutor: [add name]
### Project Sponsor: [add name]
### Github link: https://github.com/com617-industrial-2025-1/com617-HomeAutomation-eyetracking-1/tree/main

<!-- TODO add contents page  -->

## Project Summary and Introduction

The purpose of this project is to create a home automation system controlled using eye-tracking. Eye tracking technology has been used for many years to assist people with disabilites to use communication boards (Galante and Menezes 2012). Additionally, home automation, sometimes called smart homes, can also help make the homes of disabled people more accessible to them (Marko Periša et al. 2025). By combining these two technologies, we can make a solution that would allow someone with a motor disabilites to be able to perform tasks like being able to turn lights on and off without assistance, increasing their autonomy and independence. 

The software stack consists of a Javascript-based eye-tracking interface, which connected to the velbus system using node-red. The hardware used was a raspberry pi 5, which handles the on-board processing, a USB webcam, and a velbus testing kit for testing. 

The project was undertaken in three sprints, at the end of which we had a functioning Minimum Viable Product(MVP).

## Project Objectives

We were informed that the system was to be used by a child who is non-verbal and is unable to use motor functions that would enable them to use other adaptive technologies used by those with motor disabilites (WebAIM 2012b). This meant that the system's interface would have to be accessible to a child. We were also informed that due to privacy concerns processing had to be carried out on a raspberry pi that would be hosted on the home of the intended user. 

## Requirements

* Identify eye modments to identify specific reigons that are being focused on
* Movements activate VELBUS controls, which results in intended effect e.g. turning on the lights
* MQTT messages are generated to indicate changes made/actions taken
* Eye Tracking runs on raspberry pi

## Scope and Exlusions

The system is specifically designed to work with a Velbus home automation system, so it would not be able to be used with other home automation systems without modification. Due to the relatively low power of the raspberry pi, the code for eyetracking had to be kept lightweight for ideal performance. This resulted in difficulty early on as many existing libraries for gaze tracking were not designed with a low-power device such as the raspberry pi in mind. 

## Monitoring and Evaluation

Project monitoring was performed through usage of a Kanban, which was used to track what tasks needed to be done, and allowed group members to assign themselves to tasks that needed to be completed. 

<!-- discuss evaluation methods -->

## Project Organisation Structure

System development was split into three sprints that spanned over the semester. The first sprint lasted three weeks and consisted of gathering requirements and outlining a project plan we would be able to complete within the allotted time. The second sprit lasted four weeks, during which, we created an Initial Proof of Concept (PoC). This sprint involved experimenting with different solutions to find the one that worked best for our team. The final sprint lasted eight weeks, during which we polished our PoC, until we had a Minimum Viable Product (MVP), as well as preparing the final report and presentation. 

## Project Deliverables

The main deliverable of the project was the MVP itself, which consists of a Velbus test kit connected to a raspberry pi using Velbus Link, which is itself connected to a usb webcam for gaze-tracking and a monitor for viewing the interface. Other deliverables include this report and the final presentation, that is yet to be delivered as of the time of writing this report. 

## Project Milestones and Management

## Implementation

The first version of the eyetracking software was written in python, and connected to the Velbus system using OpenHab, a free-and-open-source home automation system. However, this solution worked inconsistently and after the team member who wrote it left the rest of the team were struggling to fix it. Additionally, this early implementation had features that were not necessary for an MVP, such as google gemini integration. It was decided it would be easier to start from scratch with an implementation the team was familiar with and several various options were explored, including various home automation systems such as Home Assistant, and node-red, a low-code platform based on NodeJS to handle outputs from the eye-tracking software. 

The eye-tracking software itself was written in Javascript, using the Webgazer library. Webgazer has an advantage over other libraries as it was designed with a webcam in mind, removing the need for expensive, purpose-built eye-tracking solutions. The Javascript code is connected to an html-based front-end, with `webgazer.js` serving as the code library that processes the gaze-tracking, while the javascript in `index.html	` manages gaze zones and sending data to node-red where necessary. The gaze-tracker can be calibrated by looking at the mouse cursor and clicking on the mouse at the same time. 

The front-end consists of the user's webcam footage with the gaze zones overlaid over them. If the software detects that the user's gaze has dwelled on the gaze zone for long enough, the function `sendLightSignal` is activated, which fetches the date, and, if the signal can be sent, logs the event in the browser's console and toggles the light on and off. Once the output is sent to node-red successfully, node-red sends a command to the velbus link and connected relevant devices(in this case, the light dimmer). <!-- more detail needs to be added to this section -->

## Results

Testing has found that the overall system works functionally, with some caveats that prevent the Minimum Viable Product to be able to be used by its intended user-base. The primary issue is with how the gaze-tracking software is recalibrated, requiring mouse clicks to calibrate the gaze tracker properly. In the intended use case of being used by someone with a motor disabilty, having to use a mouse may be inaccessible(WebAIM 2012a). Additionally, while the gaze-tracking is accurate enough for its current use-case, the accuracy of gaze-tracking may cause trouble if additional gaze panels were added in the future and were too close to each other. The accuracy of the gaze tracker was found to be much more inconistent for users with glasses, to the point of being unusable for them. With almost 75% of disabled people having more than one kind of impairment (Sport England 2016), it would be ideal for the system to be accessible to all disabilites, not just those with motor disabilites. 

## Conclusions and Recommendation

Overall, the progress made on the project has resulted in a successful software that can track the user's gaze and be used for home automation applications, as well as the front-end and node-red framework running entirely on the raspberry pi. However, further development could be done in order to ensure that the accessibilty of the system for its intended user-base. The problem of mouse calibration could be solved using alternative inputs, such as those detailed by (WebAIM 2012b) to allow the user to be able to calibrate the gaze tracker while being able to retain independence. Additionally, more testing, development, and experimentation would be reccomended to ensure that the gaze tracker can be used by everyone. 

Additional zones could be added for additional functionality. Some ideas for additional features that could be added to the system given by the team included an SOS zone to contact a caretaker in an emergency, as well as log messages being sent to a caretaker via phone notifications. Additional gaze zones could cover other home automation solutions offered by Velbus, such as being able to open and close blinds, and controlling heating.

## References

## Appendices

No AI has been used in the writing of this report. 

<!-- detail whether or not AI was used during development -->

