'use strict';

const gulp = require('gulp'),
    sass = require('gulp-sass'),
    concat = require('gulp-concat'),
    sourcemaps = require('gulp-sourcemaps'),
    rev = require('gulp-rev'),
    uglify = require('gulp-uglify'),
    gulpif = require('gulp-if'),
    argv = require('yargs').argv,
    pump = require('pump'),
    production = (argv.production === undefined) ? false : true;


gulp.task('sass', function () {
  return gulp.src(['./application/src/sass/*.scss'])
    .pipe(sourcemaps.init())
    .pipe(sass({outputStyle: 'compressed'}).on('error', sass.logError))
    .pipe(sourcemaps.write('.', {sourceRoot: '../src'}))
    .pipe(gulp.dest('./application/static/stylesheets'))
});

gulp.task('scripts-all', function() {
  return gulp.src([
    './application/src/js/all/vendor/polyfills/*.js',
    './application/src/js/all/vendor/govuk-template.js',
    './application/src/js/all/*.js'
    ])
    .pipe(sourcemaps.init())
    .pipe(concat('all.js'))
    .pipe(gulpif(production, uglify()))
    .pipe(sourcemaps.write('.', {sourceRoot: '../src'}))
    .pipe(gulp.dest('./application/static/javascripts'))
});

// verify uglify works
gulp.task('scripts-prod', function() {
  return gulp.src([
    './application/src/js/all/vendor/polyfills/*.js',
    './application/src/js/all/vendor/govuk-template.js',
    './application/src/js/all/*.js'
    ])
    .pipe(sourcemaps.init())
    .pipe(concat('all.js'))
    .pipe(uglify())
    .pipe(sourcemaps.write('.', {sourceRoot: '../src'}))
    .pipe(gulp.dest('./application/static/javascripts'))
});

gulp.task('scripts-charts', function(cb) {

  pump([
    gulp.src([
      './application/src/js/charts/vendor/jquery.min.js',
      './application/src/js/charts/vendor/underscore-min.js',
      './application/src/js/charts/vendor/highcharts.js',
      './application/src/js/charts/vendor/highcharts-exporting.js',
      './application/src/js/charts/rd-graph.js',
      './application/src/js/charts/rd-data-tools.js'
    ]),
    sourcemaps.init(),
    concat('charts.js'),
    gulpif(production, uglify()),
    sourcemaps.write('.', {sourceRoot: '../src'}),
    gulp.dest('./application/static/javascripts')
  ], cb);
});

gulp.task('scripts-cms', function(cb) {

  pump([
    gulp.src([
      './application/src/js/cms/*.js'
    ]),
    sourcemaps.init(),
    concat('cms.js'),
    gulpif(production, uglify()),
    sourcemaps.write('.', {sourceRoot: '../src'}),
    gulp.dest('./application/static/javascripts')
  ],
  cb
  );

});

gulp.task('watch', function () {
  gulp.watch(['./application/src/js/**/*.js', './application/src/sass/**/*.scss'], ['version']);
});

gulp.task('version-js', ['scripts-all', 'scripts-charts','scripts-cms'], function() {
    console.log(production);
  return gulp.src(['./application/static/javascripts/all.js',
    './application/static/javascripts/charts.js',
    './application/static/javascripts/cms.js'])
    .pipe(rev())
    .pipe(gulp.dest('./application/static/javascripts'))
    .pipe(rev.manifest())
    .pipe(gulp.dest('./application/static/javascripts'))
});

gulp.task('version-css', ['sass'], function() {
  return gulp.src(['./application/static/stylesheets/application.css', './application/static/stylesheets/cms.css'])
    .pipe(rev())
    .pipe(gulp.dest('./application/static/stylesheets'))
    .pipe(rev.manifest())
    .pipe(gulp.dest('./application/static/stylesheets'))
});


gulp.task('version', ['version-css', 'version-js']);

gulp.task('default',['version']);
