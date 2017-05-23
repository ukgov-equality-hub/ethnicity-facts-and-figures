# Created by Tom.Ridd at 14/05/2017
Feature: Measure page lifecyle
  # Measure pages are created, edited, approved, rejected, and finally published

Scenario: Create a fresh measure page
  Given a fresh cms with a topic page TestTopic with subtopic TestSubtopic
  When Editor creates a new measure page with name TestMeasure as a child of TestSubtopic
  Then a new measure page should exist with name TestMeasure
  And the status of measure page is draft
  And the audit log should record that Editor created TestMeasure
  And TestMeasure is internal access only

Scenario: Update a measure page
  When Editor updates some data on the TestMeasure page
  Then the TestMeasure page should reload with the correct data
  And the status of measure page is draft
  And the audit log should record that Editor saved TestMeasure
  And TestMeasure is internal access only

Scenario: Try to send an incomplete measure page to internal review
  When Editor tries to send incomplete TestMeasure page to Internal Review
  Then the status of measure page is draft
  And TestMeasure is internal access only

Scenario: Send a page to internal review
  When Editor completes all fields on the TestMeasure page
  And Editor sends the TestMeasure page to Internal Review
  Then the status of TestMeasure changes to Internal Review
  And the audit log should record that Editor submitted TestMeasure to internal review
  And TestMeasure is internal access only

Scenario: Page rejected at internal review
  When Reviewer rejects the TestMeasure page at internal review
  Then the status of TestMeasure page changes to rejected
  And the audit log should record that Reviewer rejected TestMeasure
  And TestMeasure is internal access only

Scenario: Rejected page is updated
  When Editor makes changes to the rejected TestMeasure page
  Then the rejected TestMeasure page should be updated
  And the audit log should record that Editor updated the rejected TestMeasure
  And TestMeasure is internal access only

Scenario: Resubmit rejected page
  When Editor sends the TestMeasure page to Internal Review
  Then the status of TestMeasure changes to Internal Review
  And the audit log should record that Editor submitted TestMeasure to internal review
  And TestMeasure is internal access only

Scenario: Accept page at internal review
  When Reviewer accepts the TestMeasure page
  Then the status of TestMeasure page changes to departmental review
  And the audit log should record that Reviewer accepted TestMeasure
  And TestMeasure is internal and external access

Scenario: Departmental user rejects page in departmental review
  When Department rejects the TestMeasure page at departmental review
  Then the status of TestMeasure page changes to rejected
  And the audit log should record that Department rejected TestMeasure
  And TestMeasure is internal access only

Scenario: Update a measure page after departmental rejection
  When Editor makes changes to the departmental rejected TestMeasure page
  Then the departmental rejected TestMeasure should be updated
  And the audit log should record that Editor updated department rejected TestMeasure
  And TestMeasure is internal access only

Scenario: Resubmit page rejected at departmental review
  When Editor sends the TestMeasure page to Internal Review
  Then the status of TestMeasure changes to Internal Review
  And the audit log should record that Editor submitted TestMeasure to internal review
  And TestMeasure is internal access only

Scenario: Internal reviewer accepts page previously rejected at internal review
  When Reviewer accepts the TestMeasure page
  Then the status of TestMeasure page changes to departmental review
  And the audit log should record that Reviewer accepted TestMeasure
  And TestMeasure is internal and external access

Scenario: Departmental user accepts page in departmental review
  When Department accepts the TestMeasure page at departmental review
  Then the status of TestMeasure page changes to publish
  And the audit log should record that Department accepted TestMeasure for publish
  And TestMeasure is internal and external access