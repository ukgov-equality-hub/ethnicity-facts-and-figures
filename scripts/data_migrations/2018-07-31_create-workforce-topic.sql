INSERT INTO page (guid, title, uri, page_type, description, additional_description, version, created_at, parent_guid, parent_version, db_version_id)
    VALUES ('topic_workforceandbusiness', 'Workforce and business', 'workforce-and-business', 'topic', 'Ethnic diversity in public services, staff experience and pay, self-employment and business', 'Government departments and public services collect data on ethnic diversity within their workforces, staff experience and pay. They also collect data on self-employment and running a business.

Find information on outcomes for different ethnic groups.', '1.0', now(), 'homepage', '1.0', 1);

INSERT INTO page (guid, title, uri, page_type, description, version, created_at, db_version_id, parent_guid, parent_version, position)
    VALUES ('subtopic_workforcediversity', 'Workforce diversity', 'workforce-diversity', 'subtopic', 'Workforce diversity', '1.0', now(), 1, 'topic_workforceandbusiness', '1.0', 1),
           ('subtopic_nhsstaffexperience', 'NHS staff experience', 'nhs-staff-experience', 'subtopic', 'NHS staff experience', '1.0', now(), 1, 'topic_workforceandbusiness', '1.0', 2),
           ('subtopic_publicsectorpay', 'Public sector pay', 'public-sector-pay', 'subtopic', 'Public sector pay', '1.0', now(), 1, 'topic_workforceandbusiness', '1.0', 3);
