from datetime import datetime as dt
import logging
from flask import render_template, request, jsonify, redirect
from webapp import app, pgconfig, forms


LOGGER = logging.getLogger(__name__)

CONFIG_FULL = pgconfig.get_all_config()

def get_year():
    """ Gets the current year.  Used for providing dynamic
    copyright year in the footer.

    Returns
    ----------------
    int
        Current year
    """
    return dt.now().year

@app.route('/about')
def view_about():
    return render_template('about.html',
                           year=get_year())


@app.route('/')
def view_root_url():
    return redirect_param_change_with_defaults()


@app.route('/param')
def view_app_param_not_set():
        return redirect('/param/{}'.format('max_parallel_workers_per_gather'))


@app.route('/param/<pg_param>')
def view_app_params(pg_param):
    select_html = _config_select_html(pg_param)
    config_full = pgconfig.config_to_html(CONFIG_FULL,
                                          filter_value=pg_param)
    return render_template('param.html',
                           year=get_year(),
                           config_full=config_full,
                           select_html=select_html)


@app.route('/param/change')
def redirect_param_change_with_defaults():
    return redirect('/param/change/{}/{}'.format('9.6', '12'))


@app.route('/param/change/<vers1>/<vers2>')
def view_app_param_changes(vers1, vers2):
    vers1_redirect = pgconfig.check_redirect(version=vers1)
    vers2_redirect = pgconfig.check_redirect(version=vers2)

    if vers1 == vers2:
        return redirect('/param/change')
    elif vers1 != vers1_redirect or vers2 != vers2_redirect:
        redirect_url = '/param/change/{}/{}'
        return redirect(redirect_url.format(vers1_redirect, vers2_redirect))

    vers1_html = _version_select_html(name='version_1', filter_default=vers1)
    vers2_html = _version_select_html(name='version_2', filter_default=vers2)
    try:
        config_changes = pgconfig.config_changes(CONFIG_FULL,
                                                 vers1,
                                                 vers2)
    except KeyError:
        return redirect('/param/change')
    config_changes_html = pgconfig.config_changes_html(config_changes)
    changes_stats = pgconfig.config_changes_stats(config_changes, vers1, vers2)
    return render_template('param_change.html',
                           year=get_year(),
                           config_changes=config_changes_html,
                           changes_stats=changes_stats,
                           vers1=vers1,
                           vers2=vers2,
                           vers1_html=vers1_html,
                           vers2_html=vers2_html)


@app.route('/custom')
def redirect_custom_with_defaults():
    return redirect('/custom/{}'.format('12'))


@app.route('/custom/<vers1>', methods=['GET', 'POST'])
def view_custom_config_comparison(vers1):
    vers1_html = _version_select_html(name='version_1', filter_default=vers1)
    form = forms.PostgresConfigForm()

    if form.validate_on_submit():
        config_raw = form.config_raw.data
        LOGGER.debug('User submitted config.  Length %s', len(config_raw))
        config_compare, dups = pgconfig.compare_custom_config(vers1,
                                                              config_raw)
        config_compare_full_html = pgconfig.config_changes_html(config_compare)
        
        updated_params = pgconfig.custom_config_updated_params(config_compare, vers1)
        updated_params_html = pgconfig.config_changes_html(updated_params)

        invalid_params = pgconfig.custom_config_invalid_params(config_compare, vers1)
        invalid_params_html = pgconfig.config_changes_html(invalid_params)
        change_stats = pgconfig.custom_config_changes_stats(config_compare,
                                                            vers1)
        return render_template('custom_config_result.html',
                               year=get_year(),
                               vers1=vers1,
                               vers1_html=vers1_html,
                               config_compare_full=config_compare_full_html,
                               change_stats=change_stats,
                               invalid_params=invalid_params_html,
                               updated_params=updated_params_html,
                               dups=dups)

    return render_template('custom_config.html',
                           year=get_year(),
                           vers1=vers1,
                           vers1_html=vers1_html,
                           form=form)


def _config_select_html(filter_default='max_parallel_workers_per_gather'):
    html = '<select id="selection_param" name="selection_param"> '
    options = CONFIG_FULL['parameter'].unique()
    options.sort()
    for option in options:
        if option == filter_default:
            tmp_html = '<option value="{}" selected="selected">{}</option>'
        else:
            tmp_html = '<option value="{}">{}</option>'

        html += tmp_html.format(option, option)

    # Complete the HTML object
    html += '</select>'
    return html

def _version_select_html(name, filter_default):
    html = '<select id="{name}" name="{name}"> '.format(name=name)
    options = pgconfig.VERSIONS
    for option in options:
        if option == filter_default:
            tmp_html = '<option value="{}" selected="selected">{}</option>'
        else:
            tmp_html = '<option value="{}">{}</option>'

        html += tmp_html.format(option, option)

    # Complete the HTML object
    html += '</select>'
    return html
