# Tests

This directory contains tests that cover the code for the Race Disparity Unit's “Ethnicity Facts and Figures” service. Our unit tests are found in `tests/application/` and mirror the structure of the top-level `application/` module. Our end-to-end tests are more free-form and found under `tests/functional/`.

# How our tests work

We make liberal use of [pytest fixtures](https://docs.pytest.org/en/latest/fixture.html) to minimise the amount of boilerplate setup code we need to write for each test. These are found in `conftest.py` files.

Some of our fixtures are applied automatically to all tests. Important examples are:

* A full database migration runs at the start of each test session [see `conftest:db_migration`].
* Before **every** test, all records from the database are removed (EXCEPT materialized views, which need to be refreshed on an as-needed basis within the test that needs them) [see `conftest:db_session`].
* All network requests via the `requests` library are mocked out to raise exceptions, with the aim of preventing (most) requests from reaching out to the Internet [see `conftest:requests_mocker`]

# Factory Boy
We use [Factory Boy](https://factoryboy.readthedocs.io/en/latest/introduction.html) to generate realistic model instances to test against. This replaces, in most places, the use of [pytest fixtures](https://docs.pytest.org/en/latest/fixture.html), and going forward should be the preferred way of generating test data. Using the existing factories should have a relatively small learning curve beyond knowing the interface exposed by our models. If the models change, the corresponding factories should be updated as well, in which case it is expected that you'll need to spend some time becoming familiar with how Factory Boy works.

Using these factories should be fairly intuitive once you're familiar with our models - you simply instantiate the factory and pass in parameters as keywords using the model attributes. The attributes of related models can be set during instantiation by separating with a double underscore (see examples below). Any arguments not specified will be filled in with random realistic data by the factory. Most of the factories mirror our models exactly, with some minor exceptions. Given the related nature of a lot of our models, and their dependecy on other models, using one factory may mean that multiple records are created across different tables.

The main principle used when defining our factories is that relationships of the factory that are farther away from MeasureVersion should be created. Referring to our Data Model will help appreciate the implications of this, but it should suffice to say that the MeasureVersion is considered the "centre" of the current model. Instantiating a MeasureVersion, therefore, creates many related records, whereas instantiating a Measure will create far fewer.

For example:
* MeasureFactory will create a Measure, as well as a related Subtopic and Topic.
* ClassificationFactory will create a Classification, as well as some Ethnicities, and links to those ethnicities as
  parent and child values.
* A MeasureVersionFactory will create a Measure, Subtopic, Topic, Upload, Lowest Level of Geography, etc etc.

Notably, the default MeasureVersionFactory does _not_ create any dimensions by default. An alternative factory,
MeasureVersionWithDimensionFactory, exists to do this, as creating a Dimension requires instantiating a lot of extra
models, so does not feel like an appropriate or useful default.

Example usage:
* Creating a measure:
    ```
    measure = MeasureFactory()
    ```
    Instantiates a Measure, with related Subtopic and Topic. All of these records contain random, unspecified data.
* Creating a measure version:
    ```
    measure_version = MeasureVersionFactory(status='DRAFT')
    ```
    This will create a MeasureVersion populated in the 'DRAFT' state, with all other data randomly-generated, with associated users, Measure, Subtopic, Topic, Upload, Data Source, Level of Geography, but **not** a Dimension.
* Creating a measure version with a dimension:
    ```
    measure_version = MeasureVersionWithDimensionFactory(status='PUBLISHED', dimensions__title='My dimension')
    ```
    This creates a MeasureVersion in the 'PUBLISHED' state, with all other data randomly-generated, with all associated records **including** one Dimension, and that Dimension's title will be 'My dimension'.
* Creating a dimension:
    ```
    dimension = DimensionFactory(summary="Dimension summary", dimension_chart=None)
    ```
    This will create a Dimension with the given summary, no associated Chart, and all other data randomly-generated. It **will not** generate a MeasureVersion by default. A dimension is not valid without an associated MeasureVersion, so one will need to be created and the dimension attached to it before a database commit will succeed.
* Creating a dimension and attaching it to an existing MeasureVersion:
    ```
    dimension = DimensionFactory(measue_version=measure_version)
    ```
    Creates a Dimension and sets up the `page` relationship to point to an existing MeasureVersion.
* Creating a Classification:
    ```
    classification = ClassificationFactory()
    ```
    This will create a random Classification, a set of Ethnicities (chosen from bird, cat, dog, and specific breeds of those), and some child and parent links between Classification and Ethnicity.
