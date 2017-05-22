# Created by Tom.Ridd at 14/05/2017
Feature: Measure page lifecyle
  # Measure pages are created, edited, approved, rejected, and finally published

Scenario: Create a fresh measure page
  Given a fresh cms with a topic page TestTopic with subtopic TestTopic
  When I sign in as an internal user
  And I create a new measure page with name TestMeasure as a child of TestSubtopic
  Then a new measure page should exist with name TestMeasure
  And TestMeasure should have parent TestSubtopic
  And the audit log should record that I have created TestMeasure

Scenario: Update a measure page
  When I save some data on the TestMeasure page
  Then the TestMeasure page should reload with the correct data
  And the audit log should record that I have saved TestMeasure

Scenario: Try to send an incomplete measure page to internal review
  When I try to send the TestMeasure page to Internal Review without completing all fields
  Then I am not allowed to submit to Internal Review

Scenario: Send a page to internal review
  When I complete all fields on the TestMeasure page
  And I send the TestMeasure page to Internal Review
  Then the status of TestMeasure changes to Internal Review
  And the audit log should record that I have submitted TestMeasure to internal review

Scenario: Departmental user accesses pages in internal review
  Given a departmental user
  When I sign in as departmental user
  Then I cannot access the TestMeasure page

Scenario: Internal reviewer accesses pages in internal review
  Given an internal reviewer
  When I sign in as internal reviewer
  Then I can access the TestMeasure page

Scenario: Page rejected at internal review
  When I reject the TestMeasure page at internal review
  Then the status of TestMeasure page changes to rejected
  And the audit log should record that I have rejected TestMeasure

Scenario: Rejected page is updated
  When I sign in as internal editor
  And I make changes to the rejected TestMeasure page
  Then the rejected TestMeasure page should be updated
  And the audit log should record that I have updated rejected TestMeasure

Scenario: Resubmit rejected page
  When I send the TestMeasure page to Internal Review
  Then the status of TestMeasure changes to Internal Review
  And the audit log should record that I have submitted TestMeasure to internal review

Scenario: Accept page at internal review
  When I sign in as internal reviewer
  And I accept the TestMeasure page
  Then the status of TestMeasure page changes to departmental review
  And the audit log should record that I have accepted TestMeasure

Scenario: Departmental user accesses pages in departmental review
  When I sign in as departmental user
  Then I can access the TestMeasure page

Scenario: Departmental user rejects page in departmental review
  When I reject the TestMeasure page at departmental review
  Then the status of TestMeasure page changes to rejected
  And the audit log should record that I have rejected TestMeasure

Scenario: Update a measure page after departmental rejection
  When I sign in as internal editor
  And I make changes to the departmental rejected TestMeasure page
  Then the departmental rejected TestMeasure should be updated
  And the audit log should record that I have updated department rejected TestMeasure

Scenario: Resubmit page rejected at internal review
  When I send the TestMeasure page to Internal Review
  Then the status of TestMeasure changes to Internal Review
  And the audit log should record that I have submitted TestMeasure to internal review

Scenario: Internal reviewer accepts page previously rejected at internal review
  When I sign in as internal reviewer
  And I accept the TestMeasure page
  Then the status of TestMeasure page changes to departmental review
  And the audit log should record that I have accepted TestMeasure

Scenario: Departmental user accepts page in departmental review
  When I sign in as departmental user
  And I accept the TestMeasure page at departmental review
  Then the status of TestMeasure page changes to publish
  And the audit log should record that I have accepted TestMeasure for publish