# Created by Tom.Ridd at 14/05/2017
Feature: Measure page
  # Enter feature description here

Scenario: Create a fresh measure page with minimum fields
  Given a fresh cms with a topic page TestTopic with subtopic TestSubtopic
  When I create a new measure page MeasurePage with minimum required fields
  Then measure page with minimum required fields is saved
  And measure page is in draft

Scenario: Update a measure page with default info
  When I save default data on the MeasurePage page
  Then the MeasurePage page should have default correct data

Scenario: Upload a file
  When I upload a file to a page
  Then the MeasurePage page should have one upload listed
  And the file should exist in page source folder
  And the file should contain original data

Scenario: Add a dimension to a measure page
  When I add a dimension to a measure page
  Then the MeasurePage page should have one dimension

Scenario: Edit dimension data on a measure page
  When I save data to a dimension
  Then the MeasurePage page should have one dimension
  And the MeasurePage page should have saved the dimension data

Scenario: Add chart to a dimension
  When I add a chart to a dimension
  Then the dimension should have the chart data
  And the chart json should be saved in page source

Scenario: Add table to a dimension
  When I add a table to a dimension
  Then the dimension should have the table data
  And the table json should be saved in page source
