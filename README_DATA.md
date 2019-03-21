
# EthnicityClassificationFinder and the Builders

## Ethnicity standards problem

Departments use a list of over 250 different ethnicity labels in their spreadsheets.
We need to turn the mixture of ethnicity values we get from departments into a standard list.
The list we map to has 39 values that are a variety on the ONS 2011 census values.
Also we also need to assign structure to our data: parents and order.

There are two aspects to our problem...

**Non-standard values.** The base problem arrives because departments code a standard ethnicity of "White British" in different ways

- White British
- White England/NI/Scotland/Wales
- British: White
- White: British

Converting one set of values to another set of values using a lookup table is well established.
Building the dictionary is an extensive task but this should, at least, be a solved problem. Not so for us due to...

**Contextual variation.** Any given dataset is consistent in itself. On a broad level you get contradiction.
In other words when the DfE say Asian it may mean something different to when the MoJ say Asian (and in fact does).

The worst offender is "Other". Depending on the original data set "Other" may need to become

- Other
- Other inc Chinese
- Other inc Mixed
- Other inc Asian
- Any ethnicity other than White
- Any ethnicity other than White British

Context can also change structure. For example "Chinese" maps to "Chinese" in any situation but is a child of "Asian" in the 2011 census and a child of "Other inc Chinese" in 2001.

### Solution 1: EthnicityDictionaryLookup

**EthnicityDictionaryLookup has now been removed from the codebase but notes are left here for historical interest.**

There is a standard way to share data with ambiguous columns such as Ethnicity. That is to mark each cell with the schema it's data belongs to.
When we shipped our original templates to departments we required an "Ethnicity Type" with each row of data. We could use a double lookup on Ethnicity and Type to map to useful values.

Building the *"data dictionary"* was a large task and remained ongoing throughout the lifespan. The mapping task is the job of **EthnicityDictionaryLookup**. It maps [Ethnicity, Ethnicity Type] to [Standard Ethnicity, Parent, Parent-child order]. In the event of Ethnicity Type being absent or unrecognisable we had a default as part of the dictionary.

**Problem:** This system relies on Ethnicity Type being robust and it isn't. The ideal of having a common language of Ethnicity and Classification definitions across government is only a dream at present. This results with default being used most of the time and the flexibility of DictionaryLookup could not be exploited



### Solution 2: EthnicityClassificationFinder

Solution 2 regards the **non-standard values** and **contextual variation** problems as distinct. It allows you to standardise ethnicity without having to rely on data providers or spend time cleaning Ethnicity Type data. This is possible due to the familiarity we have built with ethnicity categorisations.

In stage 1 EthnicityClassificationFinder converts raw-values received from departments into a standard list used across RDU.

In stage 2 it takes the outputs from stage 1 and determines which of known ethnicity classifications might apply. We store a list of "Ethnicity type classifications" such as "ONS 2001 5+1" and "White British and other". These contain information on how data with that Ethnicity type should be displayed.



## The Builders

ChartBuilder and TableBuilder function in roughly the same way. ChartBuilder will be detailed here and anything particular to TableBuilder should be minor

### Charts in rd_cms

Charts in the Ethnicity Facts and Figures ecosystem works on three files

- create_chart.html is the actual builder file.
- rd-chart-objects.js is a factory for building rd-chart objects.
- rd-graph.js is a renderer for rendering rd-chart objects.

Some common functions between the table builder and chart builder are also stored in rd-builder.js

On **Save** the chartbuilder builds a rd-chart object which it sends to be stored on the dimension for rendering by rd-graph. It also sends a json dump of all the current builder settings so it can recall them next time this chart is opened up.

### ChartBuilder

On the back-end it is supported by EthnicityClassificationFinder.

### How it works

Chartbuilder has the handleNewData(success) function at its heart

- User pastes excel content as text into the data box and clicks Next.
- handleNewData(success) is triggered and makes an AJAX call to the EthnicityClassificationFinder endpoint. A list of EthnicityClassificationFinder classifications with processed data is returned.
- The success function stores all the valid EthnicityClassificationFinder classifications (and their converted data) client side. It picks the first classification for preference then sets up the rest of the builder form using data from that classification.
- When changes are made to any setting chartbuilder builds a chart object and renders in the chart area using the standard values
- Save posts an AJAX call to the cms chartbuilder endpoint with a chart object and the current builder settings, both as lumps of json. These are stored as json objects in the database.
- If the builder is reopened it will fill the data text box from the settings. It then calls handleNewData(success) which builds classifications. At the end of the regular success function it uses the rest of the settings object to set up the existing chart.
