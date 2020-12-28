JINJA_API_KEYS = """<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/spcss@0.5.0">
<style>pre{white-space:wrap}body{margin-bottom:10px}</style>
<title>Active API Keys</title>

<h1>Active API Keys</h1>

{% for key in keys %}
<pre>
  <strong>Key: </strong>{{ key.key }}
  <strong>Authorized IP: </strong>{{ key.ip }}
  <strong>Expires: </strong>{{ (key.issued_at + key.expires_in) | dt }}
  
  <a href="{{ url_for('dna_api.manage_key', key=key.key) }}">Manage Key</a>
</pre>
<br />
{% endfor %}

<a href="{{ url_for('dna_api.gen_key') }}">Generate New Key</a>
<br />
"""

JINJA_API_KEY = """<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/spcss@0.5.0">
<style>pre{white-space:wrap}body{margin-bottom:10px}</style>
<title>API Key</title>

<h1>API Key</h1>

<pre>
  <strong>Key: </strong>{{ key.key }}
  <strong>Authorized IP: </strong>{{ key.ip }}
  <strong>Created: </strong> {{ key.issued_at | dt }}
  {%- if not key.is_expired() -%}
  <strong>Expires: </strong>{{ (key.issued_at + key.expires_in) | dt }}

  <a href="{{ url_for('dna_api.revoke_key', key=key.key) }}">Revoke Key</a>
  {% else %}
  Revoked.
  {%- endif -%}
</pre>
<br />

<a href="{{ url_for('dna_api.keys_index') }}">Active API Keys</a>
<br />
"""