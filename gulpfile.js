'use strict';
 
var gulp = require('gulp');
var sass = require('gulp-sass');
var concat = require('gulp-concat')
var sourcemaps = require('gulp-sourcemaps')

gulp.task('sass', function () {
  return gulp.src(['./src/sass/**/*.scss', './src/sass/**/**/*.scss', './src/sass/*.scss'])
    .pipe(sourcemaps.init())
    .pipe(sass().on('error', sass.logError))
    .pipe(sourcemaps.write())
    .pipe(gulp.dest('./application/static_site/static/stylesheets'))
})

gulp.task('scripts', function() {
  return gulp.src(['./src/js/*.js'])
    .pipe(concat('all.js'))
    .pipe(gulp.dest('./application/static_site/static/'))
})

gulp.task('watch', function () {
  gulp.watch(['./src/js/*.js', './src/sass/*.scss', './src/sass/**/*.scss', './src/sass/**/**/*.scss'], ['sass', 'scripts']);
})