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

The project used combination of Agile software development (Usage of Sprints instead of a waterfall style model, weekly scrums during classroom times) and usage of a kanban to manage tasks that needed to be completed, as well as assigning those tasks to group members. The three primary milestones were the presentations at the end of each sprint. The Presentation at the end of the first sprint was done in an informal fashion, while the presentation with the client that was supposed to happen at the end of the second sprint did not end up happening. 

## Implementation

## Results

## Conclusions and Recommendation

## References

## Appendices
<!-- **One appendix should be an AI usage declaration** -->

