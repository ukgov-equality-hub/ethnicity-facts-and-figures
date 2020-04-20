# Manually creating a report in publiser guidelines


## How to create a new summary report

1. Copy `new-summary-template.html` and rename it
2. Add your content in to the new file
3. Follow and use the styles that used in the template

### Hot to add a link to the homepage

Add a definition at `application/static_site/views.py`. Use the below example and
and update `indian-ethnic-group` to match your filename.
```@static_site_blueprint.route("/summaries/indian-ethnic-group")
def indian_ethnic_group():
    return render_template("static_site/static_pages/summaries/indian_ethnic_group.html")
```
Then link to content eg
```
 <a class="govuk-link"
               href="{{ url_for('static_site.indian_ethnic_group') }}">
              Indian
            </a>
```

## Where to store images
Please store your images under `application/src/static/images/summaries` folder
