# Created by Tom.Ridd at 14/05/2017
Feature: Measure page lifecyle
  # Measure pages are created, edited, approved, rejected, and finally published
  # This feature follows the path of one measure as it is edited, approved, and updated

Scenario: Create a fresh measure page
  Given a fresh cms with a topic page TestTopic with subtopic TestSubtopic
  When Editor creates a new measure page with name TestMeasure as a child of TestSubtopic
  Then a new measure page should exist with name TestMeasure
  And the status of TestMeasure page is draft

Scenario: Update a measure page
  When Editor updates some data on the TestMeasure page
  Then the TestMeasure page should reload with the correct data
  And the status of TestMeasure page is draft

Scenario: Try to send an incomplete measure page to internal review
  When Editor tries to send incomplete TestMeasure page to Internal Review
  Then the status of TestMeasure page is draft

Scenario: Send a page to internal review
  When Editor completes all fields on the TestMeasure page
  And Editor sends the TestMeasure page to Internal Review
  Then the status of TestMeasure is Internal Review

Scenario: Page rejected at internal review
  When Reviewer rejects the TestMeasure page at internal review
  Then the status of TestMeasure page is rejected

Scenario: Rejected page is updated
  When Editor makes changes to the rejected TestMeasure page
  Then the rejected TestMeasure page should be updated
  And the status of TestMeasure page is draft

Scenario: Resubmit rejected page
  When Editor sends the TestMeasure page to Internal Review
  Then the status of TestMeasure is Internal Review

Scenario: Accept page at internal review
  When Reviewer accepts the TestMeasure page
  Then the status of TestMeasure page is departmental review