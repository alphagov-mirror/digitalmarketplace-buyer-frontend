# coding=utf-8

from datetime import datetime
from flask import abort, render_template, request, redirect, \
    url_for, current_app

from dmutils.deprecation import deprecated
from dmutils.formats import get_label_for_lot_param
from dmutils.apiclient import HTTPError
from dmutils.formats import LOTS

from . import main
from .. import questions_loader
from ..presenters.search_presenters import (
    filters_for_lot,
    set_filter_states,
)
from ..presenters.search_results import SearchResults
from ..presenters.search_summary import SearchSummary
from ..presenters.service_presenters import Service
from ..helpers.search_helpers import (
    get_keywords_from_request, get_template_data, pagination,
    get_page_from_request, query_args_for_pagination,
    get_lot_from_request, build_search_query
)

from ..exceptions import AuthException
from .. import search_api_client, data_api_client


@main.route('/')
def index():
    template_data = get_template_data(main, {
        'title': 'Digital Marketplace'
    })
    return render_template('index.html', **template_data)


@main.route('/g-cloud')
def index_g_cloud():
    template_data = get_template_data(main, {
        'crumbs':  [
            {
                'text': 'Cloud technology and support',
            }
        ]
    })
    return render_template('index-g-cloud.html', **template_data)


@main.route('/g-cloud/framework')
def framework_g_cloud():
    template_data = get_template_data(main, {
        'crumbs': [
            {
                'text': 'Cloud technology and support',
                'link': url_for('.index_g_cloud')
            }
        ]
    })
    return render_template('content/framework-g-cloud.html', **template_data)


@main.route('/digital-services/framework')
def framework_digital_services():
    template_data = get_template_data(main, {
        'crumbs': [
            {
                'text': 'Specialists to work on digital projects',
                'link': 'https://digitalservicesstore.service.gov.uk'
            }
        ]
    })
    return render_template(
        'content/framework-digital-services.html', **template_data
    )


@main.route('/crown-hosting')
def index_crown_hosting():
    template_data = get_template_data(main, {
        'crumbs': [
            {
                'text': 'Physical datacentre space for legacy systems'
            }
        ]
    })
    return render_template('content/index-crown-hosting.html', **template_data)


@main.route('/crown-hosting/framework')
def framework_crown_hosting():
    template_data = get_template_data(main, {
        'crumbs': [
            {
                'text': 'Physical datacentre space for legacy systems',
                'link': url_for('.index_crown_hosting')
            }
        ]
    })
    return render_template(
        'content/framework-crown-hosting.html', **template_data
    )


@main.route('/buyers-guide')
def buyers_guide():
    template_data = get_template_data(main, {
        'crumbs': []
    })
    return render_template('content/buyers-guide.html', **template_data)


@main.route('/suppliers-guide')
def suppliers_guide():
    return redirect('/g-cloud/suppliers-guide', 301)


@main.route('/g-cloud/buyers-guide')
def buyers_guide_g_cloud():
    template_data = get_template_data(main, {
        'crumbs': [
            {
                'text': 'Cloud technology and support',
                'link': url_for('.index_g_cloud')
            }
        ]
    })
    return render_template(
        'content/buyers-guide-g-cloud.html', **template_data
    )


@main.route('/g-cloud/suppliers-guide')
def suppliers_guide_g_cloud():
    template_data = get_template_data(main, {
        'crumbs': [
            {
                'text': 'Cloud technology and support',
                'link': url_for('.index_g_cloud')
            }
        ]
    })
    return render_template(
        'content/suppliers-guide-g-cloud.html', **template_data
    )


@main.route('/cookies')
def cookies():
    template_data = get_template_data(main, {
        'crumbs': []
    })
    return render_template(
        'content/cookies.html', **template_data
    )


@main.route('/terms-and-conditions')
def terms_and_conditions():
    template_data = get_template_data(main, {
        'crumbs': []
    })
    return render_template(
        'content/terms-and-conditions.html', **template_data
    )


# support legacy urls generated by the grails app
@main.route('/service/<service_id>')
@deprecated(dies_at=datetime(2016, 1, 1))
def redirect_service_page(service_id):
    return redirect(url_for(
        ".get_service_by_id",
        service_id=service_id.upper()), code=301
    )


@main.route('/g-cloud/services/<service_id>')
def get_service_by_id(service_id):
    try:
        service = data_api_client.get_service(service_id)
        if service is None or service['services'].get('status') != 'published':
            abort(404, "Service ID '{}' can not be found".format(service_id))

        service_view_data = Service(service)

        try:
            # get supplier data and add contact info to service object
            supplier = data_api_client.get_supplier(
                service['services']['supplierId']
            )
            supplier_data = supplier['suppliers']
            service_view_data.meta.set_contact_attribute(
                supplier_data['contactInformation'][0].get('contactName'),
                supplier_data['contactInformation'][0].get('phoneNumber'),
                supplier_data['contactInformation'][0].get('email')
            )

        except HTTPError as e:
            abort(e.status_code)

        breadcrumb = [
            {
                'text': 'Cloud technology and support',
                'link': url_for('.index_g_cloud')
            },
            {
                'text': get_label_for_lot_param(service_view_data.lot.lower()),
                'link': url_for('.search', lot=service_view_data.lot.lower())
            }
        ]
        template_data = get_template_data(main, {
            'crumbs': breadcrumb,
            'service': service_view_data
        })
        return render_template('service.html', **template_data)
    except AuthException:
        abort(500, "Application error")
    except KeyError as e:
        abort(404, "Service ID '%s' can not be found" % service_id)


@main.route('/search')
@deprecated(dies_at=datetime(2016, 1, 1))
def redirect_search():
    return redirect(url_for(".search", **request.args), code=301)


@main.route('/g-cloud/search')
def search():
    filters = filters_for_lot(
        get_lot_from_request(request),
        questions_loader.get_builder()
    )

    response = search_api_client.search_services(
        **build_search_query(request, filters, questions_loader)
    )

    search_results_obj = SearchResults(response)

    pagination_config = pagination(
        search_results_obj.total,
        current_app.config["DM_SEARCH_PAGE_SIZE"],
        get_page_from_request(request)
    )

    search_summary = SearchSummary(
        response['meta']['total'],
        request.args,
        filters
    )

    breadcrumb = [
        {
            'text': 'Cloud technology and support',
            'link': url_for('.index_g_cloud')
        }
    ]

    label = get_label_for_lot_param(get_lot_from_request(request))
    if label:
        breadcrumb.append({'text': label})

    set_filter_states(filters, request)

    template_data = get_template_data(main, {
        'title': 'Search results',
        'current_lot': get_lot_from_request(request),
        'lots': LOTS,
        'search_keywords': get_keywords_from_request(request),
        'services': search_results_obj.search_results,
        'total': search_results_obj.total,
        'search_query': query_args_for_pagination(request.args),
        'pagination': pagination_config,
        'crumbs': breadcrumb,
        'summary': search_summary.markup(),
        'filters': filters
    })
    return render_template('search.html', **template_data)
