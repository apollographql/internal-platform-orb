# Style Guide

This CircleCI orb attempts to adhere to the following style guide:

  * Env Vars: UPPERCASE/snake_case
  * Parameters: lowercase/kebab-case
  * Job names: lowercase/kebab-case
  * Command names: lowercase/kebab-case
  * Workflow names: lowercase/kebab-case
  * Mustache-y data:

The general feeling is anything Circle related should be `kebab-case`, to match what we saw as unspoken conventions in the larger community. (Determined by examining some of Circle's own public orbs... but there's _plenty_ of contra-indicators)

JSON should adhere to [Google's JSON style guide](https://google.github.io/styleguide/jsoncstyleguide.xml?showone=Property_Name_Format#Property_Name_Format)
