'use strict';
 
var gulp = require('gulp'),
    sass = require('gulp-sass'),
    concat = require('gulp-concat'),
    sourcemaps = require('gulp-sourcemaps');

gulp.task('sass', function () {
  return gulp.src(['./application/src/sass/**/*.scss', './src/sass/**/**/*.scss', './src/sass/*.scss'])
    .pipe(sourcemaps.init())
    .pipe(sass().on('error', sass.logError))
    .pipe(sourcemaps.write())
    .pipe(gulp.dest('./application/static/stylesheets'))
});

gulp.task('scripts', function() {
  return gulp.src(['./application/src/js/*.js'])
    .pipe(concat('all.js'))
    .pipe(gulp.dest('./application/static/javascripts'))
});

gulp.task('watch', function () {
  gulp.watch(['./src/js/*.js', './src/sass/*.scss', './src/sass/**/*.scss', './src/sass/**/**/*.scss', './application/src/sass/*.scss'], ['sass', 'scripts']);
});
