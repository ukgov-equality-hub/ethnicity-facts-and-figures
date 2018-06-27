
# Harmoniser, AutoDataGenerator and Chartbuilder 2

## Ethnicity standards problem

Departments use a list of over 250 different ethnicity labels in their spreadsheets. We need to turn the mixture of ethnicity values we get from departments into a standard list.  The list we map to has 39 values that are a variety on the ONS 2011 census values. Also we also need to assign structure to our data: parents and order. 

There are two aspects to our problem...

**Non-standard values.** The base problem arrives because departments code a standard ethnicity of "White British" in different ways

- White British
- White England/NI/Scotland/Wales
- British: White
- White: British

Converting one set of values to another set of values using a lookup table is well established. Building the dictionary is an extensive task but this should, at least, be a solved problem. Not so for us due to...

**Contextual variation.** Any given dataset is consistent in itself. On a broad level you get contradiction. In other words when the DfE say Asian it may mean something different to when the MoJ say Asian (and in fact does)

The worst offender is "Other". Depending on the original data set "Other" may need to become 

- Other
- Other inc Chinese
- Other inc Mixed
- Other inc Asian
- Any ethnicity other than White
- Any ethnicity other than White British

Context can also change structure. For example "Chinese" maps to "Chinese" in any situation but is a child of "Asian" in the 2011 census and a child of "Other inc Chinese" in 2001.

### Solution 1: The Harmoniser

There is a standard way to share data with ambiguous columns such as Ethnicity. That is to mark each cell with the schema it's data belongs to. Cutting technical language when we shipped our original templates to departments we required an "Ethnicity Type" with each row of data. We could use a double lookup on Ethnicity and Type to find the final value. Building the dictionary for this was a large task and an ongoing one. The mapping task is the job of **The Harmoniser**. It maps [Ethnicity, Ethnicity Type] to [Standard Ethnicity, Parent, Parent-child order]. In the event of Ethnicity Type being absent or unrecognisable we had a default as part of the dictionary. 

**Problem:** This system relies on Ethnicity Type being robust. Not a chance. This ended up with default being used most of the time and the flexibility of the Harmoniser was not explored



### Solution 2: AutodataGenerator

Solution 2 regards the **non-standard values** and **contextual variation** problems as distinct. It allows you to standardise ethnicity without having to rely on data providers or spend time cleaning Ethnicity Type data. This is possible due to the familiarity we have built with ethnicity categorisations. 

In stage 1 AutoDataGenerator deals with non-standard values. It uses a single mapping to reduce the long list to standards.  It requires one dictionary which can be relatively simple.

In stage 2 AutoDataGenerator takes the outputs from stage 1 and applies contextual variation. We store a list of "Ethnicity type presets" such as "ONS 2001 5+1" and "White British and other". These contain information on how data with that Ethnicity type should be displayed.

AutoDataGenerator compares the list of standardised data from stage 1 to each preset and checks whether it matches up. If it does it will process the data using that preset. It returns all valid presets along with their processed data. In most instances there is only one preset that applies.

AutoDataGenerator also appends a "custom" preset which has had no processing. This means that AutoDataGenerator always returns something, even if input data doesn't fit any existing preset


## The Chartbuilders

Charts in the Ethnicity Facts and Figures ecosystem works on three files

- create_chart.html is the actual builder file. 
- rd-chart-objects.js is a factory for building rd-chart objects.
- rd-graph.js is a renderer for rendering rd-chart objects.

Some common functions between the table builder and chart builder are also stored in rd-builder.js

On **Save** the chartbuilder builds a rd-chart object which it sends to be stored on the dimension for rendering by rd-graph. It also sends a json dump of all the current builder settings so it can recall them next time this chart is opened up.

### Chartbuilder 2 

Chartbuilder 2 replaces create_chart.html with create_chart_2.html. That is all. On the back-end it is supported by AutoDataGenerator instead of Harmoniser. Also significant thought is required to handle the transition in terms of settings but nothing in the wider front-end system is different.

### How it works

Both chartbuilders have the handleNewData(success) function at their heart

- User pastes excel content as text into the data box and clicks Okay. 
- handleNewData(success) is triggered and makes an AJAX call to the AutoDataGenerator endpoint. A list of autodata presets with processed data is returned. 
- The success function stores all the valid autodata presets (and their converted data) client side. It picks the first preset for preference then sets up the rest of the builder form using data from that preset.
- When changes are made to any setting chartbuilder builds a chart object and renders in the chart area using the standard values
- Save posts an AJAX call to the cms chartbuilder endpoint with a chart object and the current builder settings, both as lumps of json. These are stored as json objects in the database.
- If the builder is reopened it will fill the data text box from the settings. It then calls handleNewData(success) which builds presets. At the end of the regular success function it uses the rest of the settings object to set up the existing chart.

### Transition

The big issue moving from Chartbuilder 1 to Chartbuilder 2 is settings. All charts have been saved with a chart_source_data object to fire up the Chartbuilder 1 screen. These settings won't work for Chartbuilder 2. Instead we have added a chart_2_source_data field to Dimension.

For transition a settings upgrade function has been written so that Chartbuilder 1 settings can be opened in Chartbuilder 2. This has been tested extensively but may not work perfectly in every case.  We are still keeping both builders active on different endpoints

- \<dimension>/create-chart
- \<dimension>/create-chart/advanced

These are accessed through a master endpoint

- \<dimension>/chartbuilder
The master endpoint uses one further new Dimension field - chart_builder_version. Its behaviour is to open the chartbuilder version specified by chart_builder_version but default to Chartbuilder 2
