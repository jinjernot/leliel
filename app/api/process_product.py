from app.core.product_template import build_product_template
from app.core.companion_template import build_template_companions, build_top_companions_by_type
from flask import render_template, current_app
import pandas as pd
import logging
from datetime import datetime, timedelta
from app.api.api_error import render_friendly_error
from app import metrics as app_metrics


def get_product_type(product_data):
    """"
    Extracts the product type from the product data.
    """
    pmoid = product_data.get('productHierarchy', {}).get(
        'productType', {}).get('pmoid')
    return current_app.config['PRODUCT_HIERARCHY'].get(pmoid)


def process_api_response(response_json, sku, locales=None, country_code=None, language_code=None, response_time=None):
    """
    Process the API response and render the product template
    """
    try:
        current_locale = f"{country_code}-{language_code}" if country_code and language_code else None
        translations = current_app.config['TRANSLATIONS'].get(language_code, current_app.config['TRANSLATIONS']['en'])
        product = response_json.get('products', {}).get(sku, {})
        is_obsolete = product.get('plcStatus') == 'Obsolete'
        product_type = get_product_type(product)
        companions = build_template_companions(response_json, sku)
        top_companions = build_top_companions_by_type(response_json, sku)
        df, df_images, df_footnotes, df_disclaimers, tech_specs_by_group, video_data = build_product_template(
            response_json)

        group_order = current_app.config.get('TECH_SPEC_GROUP_ORDER', [])

        def sort_key(group_name):

            try:
                return group_order.index(group_name)
            except ValueError:
                return len(group_order)

        sorted_tech_specs_by_group = sorted(
            tech_specs_by_group.items(), key=lambda item: (sort_key(item[0]), item[0]))
        top_components_list = []
        if product_type and product_type in current_app.config['TOP_COMPONENTS']:
            all_specs = {
                spec['tag']: spec for group in tech_specs_by_group.values() for spec in group}
            for tag in current_app.config['TOP_COMPONENTS'][product_type]:
                if tag in all_specs:
                    top_components_list.append(all_specs[tag])

        mm_config = current_app.config['MM_BLOCKS_CONFIG']
        printer_types = current_app.config['PRINTER_PRODUCT_TYPES']
        mm_blocks = []
        available_images = df_images.copy()

        mm_patterns = mm_config['TAG_PATTERNS']['PRINTER_TYPES'] if product_type in printer_types else mm_config['TAG_PATTERNS']['DEFAULT']

        for i in range(1, mm_config['ITERATIONS'] + 1):
            headline_tag = mm_patterns['headline'].format(i=i)
            support_tag = mm_patterns['support'].format(i=i)

            headline_series = df[df['tag'] == headline_tag]['value']
            support_series = df[df['tag'] == support_tag]['value']

            if not (headline_series.empty and support_series.empty) and not available_images.empty:
                image_row = available_images.iloc[0]
                mm_blocks.append({
                    'headline': headline_series.iloc[0] if not headline_series.empty else '',
                    'support': support_series.iloc[0] if not support_series.empty else '',
                    'image_url': image_row['imageUrlHttps']
                })
                available_images = available_images.drop(
                    available_images.index[0])

        feature_config = current_app.config['FEATURE_BLOCKS_CONFIG']
        feature_blocks = []

        feature_patterns = feature_config['TAG_PATTERNS'][
            'PRINTER_TYPES'] if product_type in printer_types else feature_config['TAG_PATTERNS']['DEFAULT']

        for i in range(1, feature_config['OUTER_ITERATIONS'] + 1):
            if len(feature_blocks) >= feature_config['MAX_BLOCKS']:
                break
            for j in range(1, feature_config['INNER_ITERATIONS'] + 1):
                headline_tag = feature_patterns['headline'].format(i=i, j=j)
                support_tag = feature_patterns['support'].format(i=i, j=j)
                image_url_tag = feature_patterns['image'].format(i=i, j=j)

                headline_series = df[df['tag'] == headline_tag]['value']
                support_series = df[df['tag'] == support_tag]['value']
                image_url_series = df[df['tag'] == image_url_tag]['value']

                if not headline_series.empty and not image_url_series.empty:
                    feature_blocks.append({
                        'headline': headline_series.iloc[0],
                        'support': support_series.iloc[0] if not support_series.empty else '',
                        'image_url': image_url_series.iloc[0]
                    })
                    if len(feature_blocks) >= feature_config['MAX_BLOCKS']:
                        break

        metrics_dir = current_app.config.get('METRICS_DIR', 'metrics')
        hierarchy = product.get('productHierarchy', {})
        pmoid = hierarchy.get('productType', {}).get('pmoid')
        metric_product_type = pmoid  # store pmoid; resolved to English name at display time
        metric_family = hierarchy.get('marketingSubCategory', {}).get('name')

        # Extended metrics
        plc_status = product.get('plcStatus')
        metric_category = hierarchy.get('marketingCategory', {}).get('name')
        metric_series = hierarchy.get('bigSeries', {}).get('name')
        fallback_applied = product.get('fallbackApplied', False)
        has_video = video_data is not None
        has_companions = bool(companions)
        image_count = len(df_images) if not df_images.empty else 0
        spec_group_count = len(tech_specs_by_group)

        # Check EOL: flag products with endOfSalesDate within 90 days
        eol_date = None
        end_of_sales = product.get('plcDates', {}).get('endOfSalesDate')
        if end_of_sales:
            try:
                eos = datetime.strptime(end_of_sales, '%Y-%m-%d').date()
                if eos <= (datetime.now().date() + timedelta(days=90)):
                    eol_date = end_of_sales
            except (ValueError, TypeError):
                pass

        app_metrics.record_page_view(
            metrics_dir, sku, current_locale or 'unknown',
            metric_product_type, metric_family,
            plc_status=plc_status,
            category=metric_category,
            series=metric_series,
            fallback=fallback_applied,
            response_time=response_time,
            has_video=has_video,
            has_companions=has_companions,
            image_count=image_count,
            spec_group_count=spec_group_count,
            eol_date=eol_date,
        )
        return render_template('product_template.html', df=df, tech_specs_by_group=sorted_tech_specs_by_group, df_images=df_images, companions=companions, top_companions=top_companions, df_footnotes=df_footnotes, df_disclaimers=df_disclaimers, mm_blocks=mm_blocks, feature_blocks=feature_blocks, top_components=top_components_list, video_data=video_data, locales=locales, sku=sku, current_locale=current_locale, country_names=current_app.config['COUNTRY_NAMES'], locale_names=current_app.config['LOCALE_NAMES'], translations=translations, is_obsolete=is_obsolete)
    except KeyError as e:
        logging.error(
            f"A KeyError occurred in process_api_response: {e}", exc_info=True)
        app_metrics.record_error(current_app.config.get('METRICS_DIR', 'metrics'), sku, f"{country_code}-{language_code}", f"KeyError: {e}")
        return render_friendly_error(
            message='An error occurred while preparing this product page. Please try again later.',
            status_code=500,
            title='Could not load product page'
        )
    except Exception as e:
        logging.error(
            f"An unexpected error occurred in process_api_response: {e}", exc_info=True)
        app_metrics.record_error(current_app.config.get('METRICS_DIR', 'metrics'), sku, f"{country_code}-{language_code}", str(e))
        return render_friendly_error(
            message='An unexpected error occurred while preparing this product page. Please try again later.',
            status_code=500,
            title='Could not load product page'
        )