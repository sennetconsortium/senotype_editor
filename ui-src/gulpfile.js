const gulp = require('gulp')
const stylus = require('gulp-stylus')
const header = require('gulp-header')
const { exec } = require('child_process')

const pkg = require('./package.json')
const banner = [
    '/**',
    ' * <%= pkg.name %> - <%= pkg.description %>',
    ' * @version v<%= pkg.version %>',
    ' * @link <%= pkg.homepage %>',
    ' * @date <%= date %>',
    ' */',
    ''
].join('\n')


function css() {
    return gulp
        .src('./css/main.styl')
        .pipe(
            stylus({
                compress: true
            })
        )
        .pipe(header(banner, { pkg, date: new Date() }))
        .pipe(gulp.dest('../app/static/css/'))
}

gulp.task('css', css)

function touch() {
    try {
        exec('npm run css', (error, stdout, stderr) => {})
    } catch (e) {}
}

gulp.task('touch', touch)

exports.default = function () {
    gulp.watch('css/**/*.styl', touch)
}