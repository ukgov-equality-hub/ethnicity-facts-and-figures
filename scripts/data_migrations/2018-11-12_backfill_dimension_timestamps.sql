
-- Copy created_at dates from page to dimension.
UPDATE dimension SET created_at = page.created_at from page WHERE dimension.page_id = page.guid and dimension.page_version = page.version and dimension.created_at IS NULL;

-- Copy updated_at dates from page updated_at to dimension, where they exist.
UPDATE dimension SET updated_at = page.updated_at from page WHERE dimension.page_id = page.guid and dimension.page_version = page.version and dimension.updated_at IS NULL and page.updated_at IS NOT NULL;

-- Copy updated_at dates from page created_at to dimension, where the page doesn’t have an updated_at.
UPDATE dimension SET updated_at = page.created_at from page WHERE dimension.page_id = page.guid and dimension.page_version = page.version and dimension.updated_at IS NULL and page.updated_at IS NULL;
