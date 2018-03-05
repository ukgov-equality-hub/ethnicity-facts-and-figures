# Created by Tom.Ridd at 14/05/2017
Feature: Measure page lifecyle
  # Measure pages are created, edited, approved, rejected, and finally published
  # This feature follows the path of one measure as it is edited, approved, and updated

Scenario: Create a fresh measure page
  Given a fresh cms with a topic page TestTopic with subtopic TestSubtopic
  When Editor creates a new measure page with name TestMeasure as a child of TestSubtopic
  Then a new measure page should exist with name TestMeasure with draft status

Scenario: Try to send an incomplete measure page to internal review
  When Editor tries to send incomplete TestMeasure page to Internal Review
  Then they get an error message saying page is not complete

Scenario: Update a measure page
  When Editor updates some data on the TestMeasure page
  Then the TestMeasure page should reload with the correct data

Scenario: Send a completed page to internal review
  When Editor now sends completed TestMeasure page to review
  Then the status of TestMeasure is Internal Review
