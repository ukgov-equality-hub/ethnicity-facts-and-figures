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
gulp.task('copy-assets', function () {
  return gulp.src(['./node_modules/govuk-frontend/assets/**'])
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
    './node_modules/govuk-frontend/all.js',
    './application/src/js/all/vendor/jquery.min.js',
    './application/src/js/all/vendor/polyfills/*.js',
    './application/src/js/all/vendor/govuk-template.js',
    './application/src/js/all/*.js'
  ])
    .pipe(sourcemaps.init())
    .pipe(concat('all.js', { newLine: ';' }))
    .pipe(uglify())
    .pipe(sourcemaps.write('.', { sourceRoot: '../src' }))
    .pipe(gulp.dest('./application/static/javascripts'))
});

gulp.task('compile-js-charts', function (cb) {

  pump([
    gulp.src([
      './application/src/js/charts/vendor/underscore-min.js',
      './application/src/js/charts/vendor/highcharts.js',
      './application/src/js/charts/vendor/highcharts-exporting.js',
      './application/src/js/charts/rd-graph.js',
      './application/src/js/charts/rd-data-tools.js'
    ]),
    sourcemaps.init(),
    concat('charts.js'),
    uglify(),
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
    uglify(),
    sourcemaps.write('.', { sourceRoot: '../src' }),
    gulp.dest('./application/static/javascripts')
  ],
    cb
  );

});

gulp.task('compile-js-tablebuilder2', function (cb) {
  pump([
    gulp.src([
      './application/src/js/tablebuilder2/*.js',
      './application/src/js/cms/rd-builder.js',
      './application/src/js/charts/rd-data-tools.js'
    ]),
    sourcemaps.init(),
    concat('tablebuilder2.js'),
    uglify(),
    sourcemaps.write('.', { sourceRoot: '../src' }),
    gulp.dest('./application/static/javascripts')
  ],
    cb
  );
});

gulp.task('compile-js-chartbuilder2', function (cb) {
  pump([
    gulp.src([
      './application/src/js/chartbuilder2/*.js'
    ]),
    sourcemaps.init(),
    concat('chartbuilder2.js'),
    uglify(),
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
    './application/static/javascripts/tablebuilder2.js',
    './application/static/javascripts/chartbuilder2.js'])
    .pipe(rev())
    .pipe(gulp.dest('./application/static/javascripts'))
    .pipe(rev.manifest())
    .pipe(gulp.dest('./application/static/javascripts'))
});

gulp.task('manifest-css', function () {
  return gulp.src(['./application/static/stylesheets/application.css', './application/static/stylesheets/cms.css'])
    .pipe(rev())
    .pipe(gulp.dest('./application/static/stylesheets'))
    .pipe(rev.manifest())
    .pipe(gulp.dest('./application/static/stylesheets'))
});

gulp.task('make-js', gulp.series(gulp.parallel('compile-js-all', 'compile-js-charts', 'compile-js-cms', 'compile-js-tablebuilder2', 'compile-js-chartbuilder2'), 'manifest-js'));

gulp.task('make-css', gulp.series(gulp.parallel('compile-css'), 'manifest-css'));

gulp.task('make', gulp.parallel('copy-assets', 'copy-static', 'make-css', 'make-js'));

gulp.task('default', gulp.series('make'));

gulp.task('watch', function () {
  gulp.watch(['./application/src/js/**/*.js', './application/src/sass/*.scss', './application/src/sass/**/*.scss'], gulp.series('make'));
});
