'use strict';

const gulp = require('gulp'),
  sass = require('gulp-sass'),
  concat = require('gulp-concat'),
  sourcemaps = require('gulp-sourcemaps'),
  rev = require('gulp-rev'),
  uglify = require('gulp-uglify'),
  gulpif = require('gulp-if'),
  argv = require('yargs').argv,
  pump = require('pump');


gulp.task('copy-static', function () {
  return gulp.src(['./application/src/static/**'])
    .pipe(gulp.dest('./application/static'))
})

// Copy assets from GOV.UK Frontend
gulp.task('copy-govuk-frontend-assets', function () {
  return gulp.src(['./node_modules/govuk-frontend/govuk/assets/**'])
    .pipe(gulp.dest('./application/static/assets'))
})

gulp.task('compile-css', function () {
  return gulp.src(['./application/src/sass/*.scss'])
    .pipe(sourcemaps.init())
    .pipe(sass({ outputStyle: 'compressed' }).on('error', sass.logError))
    .pipe(sourcemaps.write('.', { sourceRoot: '../src' }))
    .pipe(gulp.dest('./application/static/stylesheets'))
});

gulp.task('compile-js-all', function () {
  return gulp.src([
    './node_modules/govuk-frontend/govuk/all.js',
    './application/src/js/all/vendor/jquery.min.js',
    './application/src/js/all/vendor/polyfills/*.js',
    './application/src/js/all/vendor/govuk-template.js',
    './application/src/js/all/*.js'
  ])
    .pipe(sourcemaps.init())
    .pipe(concat('all.js', { newLine: ';' }))
    .pipe(gulpif(!process.env.DISABLE_UGLIFY, uglify()))
    .pipe(sourcemaps.write('.', { sourceRoot: '../src' }))
    .pipe(gulp.dest('./application/static/javascripts'))
});

gulp.task('compile-js-charts', function (cb) {

  pump([
    gulp.src([
      './application/src/js/charts/vendor/underscore-min.js',
      './application/src/js/charts/vendor/highcharts/v5/highcharts.js',
      './application/src/js/charts/vendor/highcharts/v5/exporting.js',
      './application/src/js/charts/vendor/highcharts/v5/export-data.js',
      './application/src/js/charts/vendor/highcharts/v5/accessibility.js',
      './application/src/js/charts/rd-graph.js',
      './application/src/js/charts/rd-data-tools.js'
    ]),
    sourcemaps.init(),
    concat('charts.js'),
    gulpif(!process.env.DISABLE_UGLIFY, uglify()),
    sourcemaps.write('.', { sourceRoot: '../src' }),
    gulp.dest('./application/static/javascripts')
  ], cb);
});

gulp.task('compile-js-cms', function (cb) {

  pump([
    gulp.src([
      './application/src/js/cms/*.js'
    ]),
    sourcemaps.init(),
    concat('cms.js'),
    gulpif(!process.env.DISABLE_UGLIFY, uglify()),
    sourcemaps.write('.', { sourceRoot: '../src' }),
    gulp.dest('./application/static/javascripts')
  ],
    cb
  );

});

gulp.task('compile-js-tablebuilder', function (cb) {
  pump([
    gulp.src([
      './application/src/js/tablebuilder/*.js',
      './application/src/js/cms/rd-builder.js',
      './application/src/js/charts/rd-data-tools.js'
    ]),
    sourcemaps.init(),
    concat('tablebuilder.js'),
    gulpif(!process.env.DISABLE_UGLIFY, uglify()),
    sourcemaps.write('.', { sourceRoot: '../src' }),
    gulp.dest('./application/static/javascripts')
  ],
    cb
  );
});

gulp.task('compile-js-chartbuilder', function (cb) {
  pump([
    gulp.src([
      './application/src/js/chartbuilder/*.js'
    ]),
    sourcemaps.init(),
    concat('chartbuilder.js'),
    gulpif(!process.env.DISABLE_UGLIFY, uglify()),
    sourcemaps.write('.', { sourceRoot: '../src' }),
    gulp.dest('./application/static/javascripts')
  ],
    cb
  );
});

gulp.task('watch', function () {
  gulp.watch(['./application/src/js/**/*.js', './application/src/sass/*.scss', './application/src/sass/**/*.scss'], gulp.series('version'));
});

gulp.task('manifest-js', function () {
  return gulp.src(['./application/static/javascripts/all.js',
    './application/static/javascripts/charts.js',
    './application/static/javascripts/cms.js',
    './application/static/javascripts/tablebuilder.js',
    './application/static/javascripts/chartbuilder.js'])
    .pipe(rev())
    .pipe(gulp.dest('./application/static/javascripts'))
    .pipe(rev.manifest())
    .pipe(gulp.dest('./application/static/javascripts'))
});

gulp.task('manifest-css', function () {
  return gulp.src(['./application/static/stylesheets/application.css'])
    .pipe(rev())
    .pipe(gulp.dest('./application/static/stylesheets'))
    .pipe(rev.manifest())
    .pipe(gulp.dest('./application/static/stylesheets'))
});

gulp.task('make-js', gulp.series(gulp.parallel('compile-js-all', 'compile-js-charts', 'compile-js-cms', 'compile-js-tablebuilder', 'compile-js-chartbuilder'), 'manifest-js'));

gulp.task('make-css', gulp.series(gulp.parallel('compile-css'), 'manifest-css'));

gulp.task('make', gulp.parallel('copy-govuk-frontend-assets', 'copy-static', 'make-css', 'make-js'));

gulp.task('default', gulp.series('make'));

gulp.task('watch', function () {
  gulp.watch(['./application/src/js/**/*.js', './application/src/sass/*.scss', './application/src/sass/**/*.scss', './gulpfile.js'], gulp.series('make'));
});
