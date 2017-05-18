# Created by Tom.Ridd at 14/05/2017
Feature: Measure page
  # Enter feature description here

Scenario: Lifecycle of a measure page
  Given I'm a signed in user
  When I create a new page
  Then a new page should exist