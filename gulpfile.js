'use strict';

var gulp = require('gulp'),
    sass = require('gulp-sass'),
    concat = require('gulp-concat'),
    sourcemaps = require('gulp-sourcemaps'),
    rev = require('gulp-rev'),
    uglify = require('gulp-uglify');

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
    .pipe(uglify())
    .pipe(sourcemaps.write('.', {sourceRoot: '../src'}))
    .pipe(gulp.dest('./application/static/javascripts'))
});

gulp.task('scripts-charts', function() {
  return gulp.src([
        './application/src/js/charts/vendor/jquery.min.js',
        './application/src/js/charts/vendor/underscore-min.js',
        './application/src/js/charts/vendor/highcharts.js',
        './application/src/js/charts/vendor/highcharts-exporting.js',
        './application/src/js/charts/rd-graph.js',
        './application/src/js/charts/rd-data-tools.js'
    ])
    .pipe(sourcemaps.init())
    .pipe(concat('charts.js'))
    .pipe(uglify())
    .pipe(sourcemaps.write('.', {sourceRoot: '../src'}))
    .pipe(gulp.dest('./application/static/javascripts'))
});

gulp.task('scripts-cms', function() {
  return gulp.src([
        './application/src/js/cms/*.js'
    ])
    .pipe(sourcemaps.init())
    .pipe(concat('cms.js'))
    .pipe(uglify())
    .pipe(sourcemaps.write('.', {sourceRoot: '../src'}))
    .pipe(gulp.dest('./application/static/javascripts'))
});

gulp.task('watch', function () {
  gulp.watch(['./application/src/js/*.js', './application/src/sass/*.scss','./application/src/sass/*.css', './application/src/sass/**/*.scss', './application/src/sass/**/**/*.scss'], ['sass', 'scripts-all',, 'scripts-charts', 'scripts-cms']);
});

gulp.task('version-js', ['scripts-all', 'scripts-charts','scripts-cms'], function() {
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


gulp.task('version', ['version-css', 'version-js'])