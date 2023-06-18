# IDS Hyyp (hawkMod)
IDS Hyyp integration for Home Assistant


![Release](https://img.shields.io/github/v/release/hawky358/hass_ids_hyyp?label=Main%20Release)

![Installs](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=86400&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.ids_hyyp.total)

There is a **[Discord](https://discord.gg/)** server for general discussions or help. **(Down for now)**

# TOC
- [Features](#features)
- [Examples](#examples)
- [Installation](#installation)
- [About](#about)
    - [Requirements](#requirements)
- [Changelog](#changelog)

# Features

- Supports multiple sites and multiple partitions which are linked to your IDS Hyyp account.
- Supports the "Alarm Control Panel" entity which is part of home assistant
- Bypass of individual zones via switch entities
  - Creates a `switch.[zone_name]` switch entity which can be used to toggle zone on/off (bypass).
    - `TRUE` / `ON` : Zone is ON i.e. not bypassed
- Multiple stay profiles.  
    *Note that the Home Assistant built in "Alarm Control Panel" entity does not support this natively so you will have to create buttons / entity cards etc. to use this feature*
    - Creates a `button.[site_name]_[partition_name]_[stay_profile_name]` button entity which can be used to arm a specific stay profile. You can also switch between stay profiles while armed in a stay profile.
    - Creates a `sensor.[site_name]_[partition_name]_status` sensor. This sensor provides more detailed feedback regarding the state of the panel. This is similar to the `"Alarm Control Panel".status` however it also supports additional stay profile names which the native entity does not.
        - Examples of statuses: `Armed`, `Disarmed`, `Triggered`, `Away Armed`, `Armed Stay`, `Armed [Stay_profile_name]`
- IDS "Automations".  
    *"Automations" is the term used in the IDS app to activate programmable outputs e.g. to open your gate or garage door.*
    - Creates a `button.[site_name]_[automation_name]` button entity. This entity pushes the "automation" button similar to pushing the button in the IDS app.
- Shows which zone triggered an alarm 
    - Creates a `binary_sensor.[zone_name]_trigger` binary sensor entity. If the alarm is triggered, this entity changes to TRUE on the zone that triggered the alarm.
        - The sensor binary_sensor.[zone name]_trigger is normally FALSE.
        - If the alarm triggers this binary sensor will turn to TRUE on the zone that has triggered the alarm.  
        *Note multiple sensors can trigger the alarm at the same time if it's armed*
        - The sensor will  remain TRUE for 1 update cycles and then go back to FALSE  
        *You should handle any home assistant triggers with automations*
        - The sensor may remain TRUE for 2 update cycles depending on how the alarm is synchronized with the update poll.
        - *Note that due to the polling time to the IDS server this currently only updates once every 30 seconds since there is no push from IDS implemented. The sensor may therefore be up to 30 seconds "late"*


# Examples
In its most basic form, IDS Hyyp supports the "Alarm Control Panel" entity which is part of Home Assistant.
This allows arming and disarming of partitions by simulating a control panel.

![panel](images/panel.gif)


Example of a simple "panel" which has for away arm

![ex1](images/awayexample.gif)

Example of a simple "panel" which has multiple stay profiles

![ex2](images/stayexample.gif)


# Installation
**HACS Method** 

Get HACS here: (https://hacs.xyz/docs/setup/download/)

Steps in 1-4 Youtube video: **http://www.youtube.com/watch?v=FGoE4XzUE38**

0) DELETE THE OLD VERSION! (If you still have the old Pre 2023.4 version by @RenierM26)
1) Add the following custom repository to HACS: https://github.com/hawky358/hass_ids_hyyp
2) Download the integration using HACS 
3) Restart Home Assistant
4) Add Hyyp integration via Settings > Devices and Services and configure via config flow. 

HACS Method is recommended. If you know how to use SSH or another uploading method, you probably don't need a guide.



# About

## What is this integration
- IDS Hyyp integration is a Home Assistant integration which allows control of IDS alarm panels equipped with the hyyp module.
- The integration works via the existing IDS servers emulating the app.


## What is "hawkMod"

- This integration was originally developed by [@RenierM26](https://github.com/RenierM26/hass_ids_hyyp). 
- With Home Assistant version 2023.4 this integration broke and there was no longer any support or updates from the original developer.
- "hawkMod" is the name of this fork which was created to fix the integration for 2023.4. The name was changed to distinguish it from the original and to prevent any confusion with the original version.
- hawkMod uses a different [modified API](https://github.com/hawky358/pyHyypApi) and has also added several features and bugfixes (See changelog below)


## Requirements

- Requires Home Assistant version 2023.4 and newer.
- Due to the integration connecting to IDS servers, the Home Assistant server requires an internet connection.

## Disclaimer
Disclaimer: I am not a programmer/developer/coder/etc. I created this fork since I want to continue using this integration. It was broken for me (2023.4), so I fixed it and thought I'd share it so other people can also continue using it.
Support, updates, bugfixes, features, etc. will be limited, but I will help where possible and will share anything I develop


<br>
<br>

---
# Changelog:

**Version 1.3.1**
- Fixed a bug where a load error ocurred if you didn't have any "triggers" (Bumped API dependency as this was fixed in the API)

**Version 1.3.0**
- Added Binary sensor which shows which zone triggered the alarm.

    The sensor binary_sensor.[zone_name]_trigger is normally FALSE.
    If the alarm triggers this binary sensor will turn to TRUE on the zone that has triggered the alarm. 
        (Note multiple sensors can trigger the alarm at the same time if it's armed) 
    The sensor will  remain TRUE for 1 update cycles and then go back to FALSE (You should handle any home assistant triggers with automations)
    The sensor may remain TRUE for 2 update cycles depending on how the alarm is synchronized with the update poll.
    Note that due to the polling time to the IDS server this currently only updates once every 30 seconds since there is no push from IDS implemented

- Bumped API dependency


**Version 1.2.2**
- Remove "Beta" from the name, since it doesn't really mean anything at this point.

**Version 1.2.1**
- Fixed a bug where the "Panel" showed disarmed even though the state attribute for the panel showed a "Stay Armed" name. This is a limitation of the home assistant alarm control panel entity. The control panel state attribute has been reverted and no longer has detailed names in the .status attribute.
- The status and name of the armed mode is now contained within a new sensor "sensor.[site]_[partition]_armed_status" and will display the various states e.g.  "Stay Arm 1" or "Stay Arm 2", disarmed etc.


**Version 1.2.0**
- Added the ability to use more than one stay profile
    - If you have more than one stay-profile, there will now be a button entity (and a service) in home assistant for each of the stay-profiles which allows you to arm each of the "Stay-Profiles" and swap between them
    - When armed to a stay profile, the stay profile name will be shown in the "armed" box

**Version 1.1.0**
- Added the ability to trigger automations
    - If you've set up any automations/triggers in the IDS app it will now be available as a "button" entity (and a service) in home assistant.

**Version 1.0.1**

- Fixed a bug which wouldn't allow set ups with multiple sites to be added.


**Version 1.0.0**

- Updated version number only
  - The integration is working and I want to start fresh with version numbers
- API Version number also updated and bumped to 1.0.0
- Changed polling to 30 seconds as test. (Don't want to be too aggressive on IDS servers)


**Version 0.0.1.7**

- Updated Readme and allowed for display on HACS

**Version 0.0.1.6** (Main changes from the original @RenierM26 version)

1) This is a fork of @francoistk 's version. 
    - Fixed the requirement that a stay profile is required for every partition
2) Reverse engineered the pyHyypApi protobuf files and recompiled. (Fixes 2023.4 compatibility) This is not a direct change to ids_hyyp, rather it's a change to the API (https://github.com/hawky358/pyHyypApi)
3) Modified dependencies in IDS_HYYP to point to new modified pyhyypapi api package
4) Changed name to IDS Hyyp (Beta)(hawkMod) to avoid potential conflicts with previous version
5) Works with 2023.4 and higher.



