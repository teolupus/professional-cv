#!/usr/bin/env python3
"""
Build script to convert cv.yaml to JSON and embed it into template.html
Usage:
    python build.py
    python build.py --cv custom_cv.yaml --template custom_template.html --theme custom_theme.yaml
"""

import yaml
import json
import sys
import argparse
from pathlib import Path


def load_yaml(filepath):
    """Load YAML file and return parsed data"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: {filepath} not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        sys.exit(1)


def load_template(filepath):
    """Load HTML template file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: {filepath} not found")
        sys.exit(1)


def generate_css_variables(theme_config):
    """Generate CSS variable declarations from theme config"""
    if not theme_config:
        return ""

    css_vars = []

    # Light mode variables
    if 'light' in theme_config:
        light_vars = []
        for key, value in theme_config['light'].items():
            css_var_name = key.replace('_', '-')
            light_vars.append(f"            --{css_var_name}: {value};")
        css_vars.append("        :root {\n" + "\n".join(light_vars) + "\n        }")

    # Dark mode variables
    if 'dark' in theme_config:
        dark_vars = []
        for key, value in theme_config['dark'].items():
            css_var_name = key.replace('_', '-')
            dark_vars.append(f"            --{css_var_name}: {value};")
        css_vars.append("\n\n        .dark {\n" + "\n".join(dark_vars) + "\n        }")

    # Scrollbar variables (add to :root)
    if 'scrollbar' in theme_config:
        scrollbar_vars = []
        for key, value in theme_config['scrollbar'].items():
            css_var_name = f"scrollbar-{key.replace('_', '-')}"
            scrollbar_vars.append(f"            --{css_var_name}: {value};")
        if scrollbar_vars:
            css_vars[0] = css_vars[0].replace("\n        }", "\n" + "\n".join(scrollbar_vars) + "\n        }")

    # Decorative variables for light theme (add to :root)
    if 'decorative_light' in theme_config:
        decorative_vars = []
        for key, value in theme_config['decorative_light'].items():
            css_var_name = f"decorative-{key.replace('_', '-')}"
            decorative_vars.append(f"            --{css_var_name}: {value};")
        if decorative_vars:
            css_vars[0] = css_vars[0].replace("\n        }", "\n" + "\n".join(decorative_vars) + "\n        }")

    # Decorative variables for dark theme (add to .dark)
    if 'decorative_dark' in theme_config and len(css_vars) > 1:
        decorative_dark_vars = []
        for key, value in theme_config['decorative_dark'].items():
            css_var_name = f"decorative-{key.replace('_', '-')}"
            decorative_dark_vars.append(f"            --{css_var_name}: {value};")
        if decorative_dark_vars:
            css_vars[1] = css_vars[1].replace("\n        }", "\n" + "\n".join(decorative_dark_vars) + "\n        }")

    # Logo gradient variables (add to :root)
    if 'logo_gradients' in theme_config:
        logo_vars = []
        for key, value in theme_config['logo_gradients'].items():
            css_var_name = f"logo-{key.replace('_', '-')}"
            logo_vars.append(f"            --{css_var_name}: {value};")
        if logo_vars:
            css_vars[0] = css_vars[0].replace("\n        }", "\n" + "\n".join(logo_vars) + "\n        }")

    return "\n".join(css_vars)


def embed_theme(template, theme_config):
    """Replace theme color placeholders with values from theme config"""
    if not theme_config:
        return template

    # Generate CSS variables from theme config
    css_variables = generate_css_variables(theme_config)

    # Replace the existing :root and .dark CSS variable blocks
    # Look for the pattern between :root { and the end of .dark { }
    import re

    # Pattern to match from :root { to the end of .dark { }
    pattern = r':root\s*\{[^}]+\}\s*\.dark\s*\{[^}]+\}'

    if re.search(pattern, template):
        template = re.sub(pattern, css_variables, template)

    # Also update scrollbar colors if present
    if 'scrollbar' in theme_config:
        scrollbar = theme_config['scrollbar']
        if 'thumb' in scrollbar:
            template = template.replace('background: #313847;', f"background: var(--scrollbar-thumb);")
        if 'thumb_hover' in scrollbar:
            template = template.replace('background: #3f4759;', f"background: var(--scrollbar-thumb-hover);")

    return template


def generate_json_ld(data):
    """
    JSON-LD is now generated dynamically by JavaScript in the template.
    This function returns a comment placeholder for backwards compatibility.
    """
    return '<!-- JSON-LD Schema generated dynamically by JavaScript -->'


def embed_seo(template, data):
    """Inject SEO tags and JSON-LD into template"""
    basics = data.get('basics', {})

    # 1. Page Title
    page_title = f"{basics.get('name')} - {basics.get('label')}"
    template = template.replace('{{ PAGE_TITLE }}', page_title)

    # 2. Meta Description (escape quotes)
    description = basics.get('intro', {}).get('text', '').replace('"', '&quot;')
    # Remove newlines for meta tag
    description = ' '.join(description.split())
    template = template.replace('{{ META_DESCRIPTION }}', description)

    # 3. JSON-LD
    json_ld = generate_json_ld(data)
    template = template.replace('{{ JSON_LD }}', json_ld)

    return template


def embed_data(template, data):
    """Replace placeholder with JSON data in template"""
    json_data = json.dumps(data, indent=2, ensure_ascii=False)

    # Remove the placeholder comment
    template = template.replace('        // CV Data Placeholder - Will be replaced by build script\n', '')

    return template.replace('{{ CV_DATA }}', json_data)


def save_output(filepath, content):
    """Save the generated HTML to file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"✓ Successfully generated {filepath}")
    except IOError as e:
        print(f"Error writing to {filepath}: {e}")
        sys.exit(1)


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Build CV website by embedding YAML data and theme into HTML template',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py
  python build.py --cv my_cv.yaml
  python build.py --template custom_template.html --theme dark_theme.yaml
  python build.py --cv my_cv.yaml --template my_template.html --theme my_theme.yaml --output my_cv.html
        """
    )

    parser.add_argument(
        '--cv',
        type=str,
        default='cv.yaml',
        help='Path to CV YAML file (default: cv.yaml)'
    )

    parser.add_argument(
        '--template',
        type=str,
        default='template.html',
        help='Path to HTML template file (default: template.html)'
    )

    parser.add_argument(
        '--theme',
        type=str,
        default='theme.yaml',
        help='Path to theme configuration YAML file (default: theme.yaml)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='index.html',
        help='Path to output HTML file (default: index.html)'
    )

    return parser.parse_args()


def main():
    """Main build process"""
    args = parse_arguments()

    # Define file paths from arguments
    yaml_file = Path(args.cv)
    template_file = Path(args.template)
    theme_file = Path(args.theme)
    output_file = Path(args.output)

    print("Building CV website...")
    print(f"  Reading CV data from {yaml_file}...")
    cv_data = load_yaml(yaml_file)

    print(f"  Reading template from {template_file}...")
    template = load_template(template_file)

    # Load theme configuration if file exists
    theme_config = None
    if theme_file.exists():
        print(f"  Reading theme configuration from {theme_file}...")
        theme_config = load_yaml(theme_file)
        print("  Applying theme colors...")
        template = embed_theme(template, theme_config)
    else:
        print(f"  Note: Theme file {theme_file} not found, using template defaults")

    print("  Injecting SEO Key tags and Linked Data...")
    template = embed_seo(template, cv_data)

    print("  Converting YAML to JSON and embedding...")
    html_content = embed_data(template, cv_data)

    print(f"  Writing output to {output_file}...")
    save_output(output_file, html_content)

    print(f"\n✓ Build complete! Open {output_file} in your browser to view your CV.")


if __name__ == '__main__':
    main()
