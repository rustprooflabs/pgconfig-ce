from datetime import datetime as dt
import logging
from flask import render_template, redirect
from webapp import app, pgconfig


LOGGER = logging.getLogger(__name__)


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
    return redirect_param_change()


@app.route('/param')
def view_app_param_not_set():
        return redirect('/param/{}'.format('max_parallel_workers_per_gather'))



@app.route('/param/<pg_param>')
def view_app_params(pg_param):
    select_html = get_param_select_html(pg_param)
    param_details = pgconfig.get_pg_param_over_versions(pg_param)
    return render_template('param2.html',
                           year=get_year(),
                           param_details=param_details,
                           select_html=select_html)



@app.route('/param/change/<vers1>/<vers2>')
def view_app_param_changes_v2(vers1, vers2):
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
        config_changes = pgconfig.config_changes(vers1, vers2)
    except ValueError:
        return redirect('/param/change')

    config_changes_html = pgconfig.config_changes_html(config_changes)
    changes_stats = pgconfig.config_changes_stats(config_changes)
    return render_template('param_change2.html',
                           year=get_year(),
                           config_changes=config_changes_html,
                           changes_stats=changes_stats,
                           vers1=vers1,
                           vers2=vers2,
                           vers1_html=vers1_html,
                           vers2_html=vers2_html)


@app.route('/param/change')
def redirect_param_change():
    return redirect('/param/change/{}/{}'.format('15', '16'))


@app.route('/custom')
def redirect_custom_with_defaults():
    """Route supporting removed feature. If users have this route bookmarked,
    don't just 404 on them.  Gives hint at query to run to get the data directly
    in their database.
    """
    return redirect('/custom/{}'.format('16'))


@app.route('/custom/<vers1>', methods=['GET', 'POST'])
def view_custom_config_comparison(vers1):
    """Route supporting removed feature. If users have this route bookmarked,
    don't just 404 on them.  Gives hint at query to run to get the data directly
    in their database.
    """
    return render_template('custom_config.html',
                           year=get_year(),
                           vers1=None,
                           vers1_html=None,
                           form=None)



def get_param_select_html(filter_default: str='max_parallel_workers_per_gather') -> str:
    """Returns HTML of parameter options to select from on the "single parameter"
    page.

    Parameters
    ------------------------------------
    filter_default : str
        Default value: max_parallel_workers_per_gather

    Returns
    ------------------------------------
    html : str
    """
    html = '<select id="selection_param" name="selection_param"> '
    options = pgconfig.get_all_postgres_parameters()
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
