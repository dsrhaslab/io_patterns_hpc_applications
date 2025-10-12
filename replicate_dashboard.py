import argparse
import requests
import json
import logging
from datetime import datetime
from elasticsearch import Elasticsearch
from copy import deepcopy

# Configure verbose logging
logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger("DashboardCloner")

class DashboardCloner:
    def __init__(self, kibana_url, auth, es_host):
        self.kibana_url = kibana_url.rstrip('/')
        self.auth = auth
        self.headers = {
            'kbn-xsrf': 'true',
            'Content-Type': 'application/json'
        }
        self.es = Elasticsearch(
            es_host,
            basic_auth=auth,
            verify_certs=False,
            request_timeout=30
        )
        logger.debug(f"Initialized Elasticsearch client for {es_host}")
        logger.debug(f"Initialized cloner for Kibana at {self.kibana_url}")

    # Elasticsearch data retrieval functions
    def get_session_time_range(self, session_name):
        """Get the earliest and latest timestamps for a session from Elasticsearch"""
        logger.info(f"Fetching time range for session: {session_name}")
        try:
            response = self.es.search(
                index="*",
                body=self._build_time_range_query(session_name)
            )
            return self._parse_time_range_response(response, session_name)
        except Exception as e:
            logger.error(f"Error retrieving time range for {session_name}: {str(e)}")
            return (None, None)

    def _build_time_range_query(self, session_name):
        return {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"session_name.keyword": session_name}},
                        {"exists": {"field": "timestamp"}}
                    ]
                }
            },
            "aggs": {
                "min_time": {"min": {"field": "timestamp"}},
                "max_time": {"max": {"field": "timestamp"}}
            }
        }

    def _parse_time_range_response(self, response, session_name):
        if 'aggregations' not in response:
            logger.warning(f"No matching documents found for session {session_name}")
            return (None, None)

        min_time = response["aggregations"]["min_time"].get("value_as_string")
        max_time = response["aggregations"]["max_time"].get("value_as_string")

        if not min_time or not max_time:
            logger.warning(f"No valid timestamps found for session {session_name}")
            return (None, None)

        logger.debug(f"Time range for {session_name}: {min_time} to {max_time}")
        return (min_time, max_time)

    def get_session_nodes(self, session_name):
        """Get unique nodes associated with a session from Elasticsearch"""
        logger.info(f"Fetching nodes for session: {session_name}")
        try:
            response = self.es.search(
                index="*",
                body=self._build_nodes_query(session_name)
            )
            return self._parse_nodes_response(response, session_name)
        except Exception as e:
            logger.error(f"Error retrieving nodes for {session_name}: {str(e)}")
            return []

    def _build_nodes_query(self, session_name):
        return {
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"session_name.keyword": session_name}},
                        {"exists": {"field": "node.keyword"}}
                    ]
                }
            },
            "aggs": {
                "unique_nodes": {
                    "terms": {
                        "field": "node.keyword",
                        "size": 10000,
                        "order": {"_key": "asc"}
                    }
                }
            }
        }

    def _parse_nodes_response(self, response, session_name):
        if 'aggregations' not in response:
            logger.warning(f"No node data found for session {session_name}")
            return []

        buckets = response["aggregations"]["unique_nodes"].get("buckets", [])
        nodes = [bucket["key"] for bucket in buckets if "key" in bucket]
        logger.debug(f"Found {len(nodes)} nodes for session {session_name}")
        return nodes

    # Dashboard handling functions
    def get_dashboard(self, dashboard_id):
        """Retrieve dashboard via Kibana API"""
        logger.debug(f"Fetching dashboard {dashboard_id}")
        url = f"{self.kibana_url}/api/saved_objects/dashboard/{dashboard_id}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error getting dashboard: {e.response.text}")
        except Exception as e:
            logger.error(f"General error getting dashboard: {str(e)}", exc_info=True)
        return None

    def clone_dashboard(self, base_dashboard, session_name, time_range, base_nodes, nodes):
        """Orchestrate dashboard cloning process"""
        logger.info(f"Starting clone process for {session_name}")
        try:
            node_mapping = self._create_node_mapping(base_nodes,nodes)
            export_data = self._export_dashboard(base_dashboard['id'])
            processed_data = self._process_exported_data(export_data, base_dashboard, 
                                                       session_name, time_range, node_mapping)
            return self._import_dashboard(processed_data, session_name)
        except Exception as e:
            logger.error(f"Error cloning dashboard: {str(e)}", exc_info=True)
            return None

    def _create_node_mapping(self, base_nodes, new_nodes):
        """Create mapping between base nodes and new session nodes"""

        node_mapping = {}
        for old, new in zip(base_nodes, new_nodes):
            old_short = old.split('.', 1)[0]
            new_short = new.split('.', 1)[0]
            node_mapping[old] = new
            node_mapping[old_short] = new_short
            logger.debug(f"Added node mapping: {old}→{new} ({old_short}→{new_short})")
        
        return node_mapping

    def _export_dashboard(self, dashboard_id):
        """Export dashboard as NDJSON"""
        logger.debug(f"Exporting base dashboard {dashboard_id}")
        response = requests.post(
            f"{self.kibana_url}/api/saved_objects/_export",
            json={"objects": [{"type": "dashboard", "id": dashboard_id}], "includeReferencesDeep": True},
            headers=self.headers,
            auth=self.auth
        )
        response.raise_for_status()
        return response.text

    def _process_exported_data(self, export_data, base_dashboard, session_name, time_range, node_mapping):
        """Process exported NDJSON data"""
        dashboard_ndjson = []
        new_dashboard_id = f"{base_dashboard['id']}_{session_name}"

        for line in export_data.split('\n'):
            if not line.strip():
                continue
            
            obj = json.loads(line)
            obj_type = obj.get('type')

            if obj_type == 'dashboard':
                self._process_dashboard_object(obj, new_dashboard_id, session_name, time_range, node_mapping)
            elif obj_type == 'lens':
                self._process_lens_object(obj, time_range, node_mapping)

            dashboard_ndjson.append(json.dumps(obj))

        return dashboard_ndjson

    def _process_dashboard_object(self, obj, new_id, session_name, time_range, node_mapping):
        """Process dashboard object in exported data"""
        logger.debug(f"Processing dashboard {obj.get('id')}")
        obj['id'] = new_id
        obj['attributes']['title'] = f"System Overview - {session_name}"
        obj['attributes']['timeRestore'] = True
        obj['attributes']['timeFrom'] = time_range[0]
        obj['attributes']['timeTo'] = time_range[1]

        if 'panelsJSON' in obj['attributes']:
            panels = json.loads(obj['attributes']['panelsJSON'])
            self._process_panels(panels, time_range, node_mapping)
            obj['attributes']['panelsJSON'] = json.dumps(panels)

    def _process_panels(self, panels, time_range, node_mapping):
        """Process dashboard panels"""
        logger.debug(f"Processing {len(panels)} panels")
        for panel in panels:
            self._update_panel_title(panel, node_mapping)
            self._clear_panel_time_range(panel)
            
            # Process embedded lens visualization if present
            if panel.get('type') == 'lens' and 'embeddableConfig' in panel:
                self._process_panel_lens_config(panel['embeddableConfig'], time_range, node_mapping)


    def _process_panel_lens_config(self, embeddable_config, time_range, node_mapping):
        """Process lens configuration embedded in a panel with enhanced error handling"""
        logger.debug("Processing embedded lens configuration")

        try:
            attributes = embeddable_config.get('attributes', {})
            if 'state' not in attributes:
                logger.debug("No state found in embedded lens config")
                return

            # Handle stringified JSON state
            state_str = attributes['state']
            state = json.loads(state_str) if isinstance(state_str, str) else state_str

            # Process state modifications
            self._update_lens_time_range(state, time_range)
            self._process_datasource_states(state, node_mapping)
            self._process_visualization_state(state, node_mapping)

            # Stringify the state back if it was originally a string
            if isinstance(state_str, str):
                attributes['state'] = json.dumps(state)
            else:
                attributes['state'] = state

            # Update title in embeddable config if exists
            if 'title' in attributes:
                original = attributes['title']
                for old, new in node_mapping.items():
                    attributes['title'] = attributes['title'].replace(old, new)
                logger.debug(f"Updated embedded lens title: {original} → {attributes['title']}")

        except Exception as e:
            logger.error(f"Error processing embedded lens config: {str(e)}")
            logger.debug(f"Problematic lens state: {attributes.get('state', 'NO STATE FOUND')}", exc_info=True)

    def _update_panel_title(self, panel, node_mapping):
        """Update panel title with node replacements"""
        if 'title' in panel:
            original = panel['title']
            for old, new in node_mapping.items():
                panel['title'] = panel['title'].replace(old, new)
            logger.debug(f"Panel title updated: {original} → {panel['title']}")

    def _clear_panel_time_range(self, panel):
        """Clear panel-specific time ranges"""
        if 'embeddableConfig' in panel and 'timeRange' in panel['embeddableConfig']:
            logger.debug("Clearing panel time range")
            panel['embeddableConfig'].pop('timeRange', None)

    def _process_lens_object(self, obj, time_range, node_mapping):
        """Process lens visualization object"""
        logger.debug(f"Processing lens {obj.get('id')}")
        attributes = obj.get('attributes', {})
        state = self._parse_lens_state(attributes.get('state'))

        self._update_lens_metadata(attributes, node_mapping)
        self._update_lens_time_range(state, time_range)
        self._process_datasource_states(state, node_mapping)
        self._process_visualization_state(state, node_mapping)

        attributes['state'] = json.dumps(state) if isinstance(state, dict) else state
        obj['attributes'] = attributes

    def _parse_lens_state(self, state):
        """Parse lens state from string to dictionary"""
        return json.loads(state) if isinstance(state, str) else state or {}

    def _update_lens_metadata(self, attributes, node_mapping):
        """Update lens metadata fields"""
        for field in ['title', 'description']:
            if field in attributes:
                original_content = attributes[field]
                for old, new in node_mapping.items():
                    attributes[field] = attributes[field].replace(old, new)
                logger.debug(f"Updated {field}: {original_content} → {attributes[field]}")

    def _update_lens_time_range(self, state, time_range):
        """Update time range in lens state while preserving existing query properties"""
        original_query = state.get('query', {})

        state['query'] = {
            **original_query,
            'timeRange': {
                'from': time_range[0],
                'to': time_range[1],
                'mode': 'absolute'
            }
        }
        logger.debug(f"Updated time range while preserving query: {original_query} → {state['query']}")

    def _process_datasource_states(self, state, node_mapping):
        """Process datasource states in lens"""
        if 'datasourceStates' in state:
            logger.debug("Processing datasource states")
            ds_states = state['datasourceStates']
            if 'indexpattern' in ds_states:
                layers = ds_states['indexpattern'].get('layers', {})
                logger.debug(f"Found {len(layers)} index pattern layers")
                self._process_layer_columns(layers, node_mapping)

    def _process_layer_columns(self, layers, node_mapping):
        """Process columns in each layer for filter and label replacements"""
        for layer_id, layer in layers.items():
            logger.debug(f"Processing layer {layer_id}")
            columns = layer.get('columns', {})
            for col_id, column in columns.items():
                self._replace_node_references(column, node_mapping)
                self._update_column_labels(column, node_mapping)

    def _replace_node_references(self, column, node_mapping):
        """Replace node references in column filters"""
        if 'filter' in column and 'query' in column['filter']:
            original_query = column['filter']['query']
            new_query = original_query
            for old_node, new_node in node_mapping.items():
                new_query = new_query.replace(old_node, new_node)
            column['filter']['query'] = new_query
            logger.info(f"Filter replacement complete: {original_query} → {new_query}")

    def _update_column_labels(self, column, node_mapping):
        """Update labels in the column"""
        if 'label' in column:
            original_label = column['label']
            for old, new in node_mapping.items():
                column['label'] = column['label'].replace(old, new)
            logger.debug(f"Label updated: {original_label} → {column['label']}")

    def _process_visualization_state(self, state, node_mapping):
        """Process visualization state in lens"""
        if 'visualization' in state:
            logger.debug("Processing visualization state")
            viz = state['visualization']
            self._update_axis_titles(viz, node_mapping)
            self._update_series_labels(viz, node_mapping)

    def _update_axis_titles(self, viz, node_mapping):
        """Update axis titles in visualization"""
        if 'axes' in viz:
            logger.debug(f"Processing {len(viz['axes'])} axes")
            for axis_name, axis_config in viz['axes'].items():
                if 'title' in axis_config:
                    original_title = axis_config['title']
                    for old, new in node_mapping.items():
                        axis_config['title'] = axis_config['title'].replace(old, new)
                    logger.debug(f"Axis title updated: {original_title} → {axis_config['title']}")

    def _update_series_labels(self, viz, node_mapping):
        """Update series labels in visualization"""
        if 'layers' in viz:
            logger.debug(f"Processing {len(viz['layers'])} visualization layers")
            for layer in viz['layers']:
                if 'series' in layer:
                    logger.debug(f"Processing {len(layer['series'])} series")
                    for series in layer['series']:
                        if 'label' in series:
                            original_label = series['label']
                            for old, new in node_mapping.items():
                                series['label'] = original_label.replace(old, new)
                            logger.debug(f"Series label updated: {original_label} → {series['label']}")

    def _import_dashboard(self, dashboard_ndjson, session_name):
        """Import modified dashboard back to Kibana"""
        logger.debug("Starting dashboard import")
        response = requests.post(
            f"{self.kibana_url}/api/saved_objects/_import?createNewCopies=true",
            files={'file': ('dashboard.ndjson', '\n'.join(dashboard_ndjson), 'application/ndjson')},
            headers={'kbn-xsrf': 'true'},
            auth=self.auth
        )
        response.raise_for_status()
        dashboard_url = f"{self.kibana_url}/app/dashboards#/view/{session_name}"
        logger.info(f"Successfully created dashboard at {dashboard_url}")
        return dashboard_url

    def create_session_dashboards(self, base_dashboard_id, session_names):
        """Main workflow to create dashboards for multiple sessions"""
        logger.info(f"Starting dashboard creation process for {len(session_names)} sessions")
        base_dashboard = self.get_dashboard(base_dashboard_id)
        base_dashboard_session_name = base_dashboard['attributes']['title'].split('-')[1].strip()
        base_nodes = self.get_session_nodes(base_dashboard_session_name)
        
        if not base_dashboard:
            logger.error("Aborting due to base dashboard retrieval failure")
            return None
            
        dashboard_urls = []
        
        for session in session_names:
            logger.info(f"\nProcessing session: {session}")
            time_range = self.get_session_time_range(session)
            nodes = self.get_session_nodes(session)
            
            if not time_range[0] or not time_range[1]:
                logger.error(f"Skipping session {session} - invalid time range")
                continue
                
            logger.debug(f"Session time range: {time_range}")
            logger.debug(f"Session nodes: {nodes}")
            
            dashboard_url = self.clone_dashboard(
                base_dashboard,
                session,
                time_range,
                base_nodes,
                nodes
            )
            
            if dashboard_url:
                dashboard_urls.append(dashboard_url)
                logger.info(f"Successfully created dashboard for {session}")
            else:
                logger.error(f"Failed to create dashboard for {session}")
        
        return dashboard_urls

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clone Kibana dashboards with session-specific filters')
    parser.add_argument('--kibana-url', required=True, help='Kibana URL (e.g., http://localhost:5601)')
    parser.add_argument('--es-host', required=True, help='Elasticsearch URL (e.g., http://localhost:9200)')
    parser.add_argument('--es-user', required=True, help='Elasticsearch username')
    parser.add_argument('--es-pass', required=True, help='Elasticsearch password')
    parser.add_argument('--base-dashboard', required=True, help='Base dashboard ID to clone')
    parser.add_argument('--sessions', nargs='+', required=True, help='Session names to create dashboards for')
    
    args = parser.parse_args()
    
    logger.info("Starting dashboard cloner with parameters:")
    logger.info(f"Kibana URL: {args.kibana_url}")
    logger.info(f"Base dashboard ID: {args.base_dashboard}")
    logger.info(f"Sessions to process: {args.sessions}")
    
    cloner = DashboardCloner(
        kibana_url=args.kibana_url,
        auth=(args.es_user, args.es_pass),
        es_host=args.es_host
    )
    
    dashboard_urls = cloner.create_session_dashboards(
        base_dashboard_id=args.base_dashboard,
        session_names=args.sessions
    )
    
    if dashboard_urls:
        logger.info("\nSuccessfully created dashboards:")
        for url in dashboard_urls:
            logger.info(f" - {url}")
    else:
        logger.error("No dashboards were created")