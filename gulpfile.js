'use strict';

var gulp = require('gulp'),
    sass = require('gulp-sass'),
    concat = require('gulp-concat'),
    sourcemaps = require('gulp-sourcemaps'),
    rev = require('gulp-rev');

gulp.task('sass', function () {
  return gulp.src(['./application/src/sass/*.scss'])
    .pipe(sourcemaps.init())
    .pipe(sass().on('error', sass.logError))
    .pipe(sourcemaps.write())
    .pipe(gulp.dest('./application/static/stylesheets'))
});

gulp.task('scripts', function() {
  return gulp.src(['./application/src/js/vendor/polyfills/*.js', './application/src/js/*.js'])
    .pipe(concat('all.js'))
    .pipe(gulp.dest('./application/static/javascripts'))
});

gulp.task('watch', function () {
  gulp.watch(['./application/src/js/*.js', './application/src/sass/*.scss','./application/src/sass/*.css', './application/src/sass/**/*.scss', './application/src/sass/**/**/*.scss'], ['sass', 'scripts']);
});

gulp.task('version-js', ['scripts'], function() {
  var out_directory = process.argv[process.argv.length - 1];
  return gulp.src(['./application/static/javascripts/all.js'])
    .pipe(rev())
    .pipe(gulp.dest(out_directory))
    .pipe(rev.manifest())
    .pipe(gulp.dest(out_directory))
});

gulp.task('version-css', ['sass'], function() {
  var out_directory = process.argv[process.argv.length - 1];
  return gulp.src(['./application/static/stylesheets/application.css'])
    .pipe(rev())
    .pipe(gulp.dest(out_directory))
    .pipe(rev.manifest())
    .pipe(gulp.dest(out_directory))
});
