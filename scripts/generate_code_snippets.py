#!/usr/bin/env python3
"""
Generate code snippet files for report documentation
Extracts key implementation sections from city_traffic_simulator.py
"""
import os
import re

# Key implementation sections to extract
CODE_SECTIONS = {
    "multi_metric_raft_election": {
        "function": "_run_cluster_election",
        "title": "Multi-Metric Raft Election",
        "description": "Multi-metric scoring for cluster head election using trust, connectivity, stability, centrality, and tenure"
    },
    "co_leader_succession": {
        "function": "_elect_co_leader",
        "title": "Co-Leader Succession",
        "description": "Automatic co-leader promotion when primary leader fails"
    },
    "poa_malicious_detection": {
        "function": "_detect_malicious_nodes_poa",
        "title": "PoA Malicious Detection",
        "description": "Proof-of-Authority based malicious node detection with cluster-scoped voting"
    },
    "relay_node_election": {
        "function": "_elect_relay_nodes",
        "title": "Relay Node Election",
        "description": "Multi-hop relay node selection for out-of-range cluster members"
    },
    "boundary_node_election": {
        "function": "_elect_boundary_nodes",
        "title": "Boundary Node Election",
        "description": "Inter-cluster boundary node election for cluster-to-cluster communication"
    },
    "v2v_message_broadcast": {
        "function": "broadcast_v2v_message",
        "title": "V2V Message Broadcast",
        "description": "Vehicle-to-vehicle message broadcasting with multi-hop relay support"
    },
    "collision_detection": {
        "function": "check_collision_risk",
        "title": "Collision Detection",
        "description": "Predictive collision detection using future position calculation"
    },
    "cluster_merging": {
        "function": "_merge_overlapping_clusters",
        "title": "Cluster Merging Algorithm",
        "description": "Prevents sub-clustering by merging overlapping clusters based on leader proximity and member overlap"
    }
}

def extract_function(filepath, function_name):
    """Extract function code from file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find function definition
        pattern = rf'^\s*def {re.escape(function_name)}\s*\('
        match = re.search(pattern, content, re.MULTILINE)
        
        if not match:
            return None
        
        func_start = match.start()
        lines = content[func_start:].split('\n')
        
        # Get base indentation
        func_lines = [lines[0]]
        base_indent = len(lines[0]) - len(lines[0].lstrip())
        
        # Extract until next function at same or lower indentation
        for i, line in enumerate(lines[1:], 1):
            # Check if we hit next function definition at same level
            if line.strip() and not line.startswith(' ' * (base_indent + 1)):
                if line.strip().startswith('def '):
                    break
            func_lines.append(line)
            
            # Stop if we've collected too much (safety)
            if i > 200:
                break
        
        return '\n'.join(func_lines).rstrip()
    except Exception as e:
        print(f"Error extracting {function_name}: {e}")
        return None

# Main execution
print("=" * 70)
print("📝 CODE SNIPPET EXTRACTOR FOR REPORT")
print("=" * 70)
print()

source_file = 'city_traffic_simulator.py'
output_dir = 'report_assets/code_snippets'

if not os.path.exists(source_file):
    print(f"❌ Error: {source_file} not found!")
    exit(1)

os.makedirs(output_dir, exist_ok=True)

print(f"📂 Source: {source_file}")
print(f"📂 Output: {output_dir}/\n")

snippets_md = "# Code Implementation Snippets\n\n"
snippets_md += "Generated from city_traffic_simulator.py for capstone report documentation.\n\n"
snippets_md += "---\n\n"

extracted_count = 0
failed_count = 0

for key, details in CODE_SECTIONS.items():
    function_name = details['function']
    title = details['title']
    description = details['description']
    
    print(f"Extracting: {title}")
    print(f"  Function: {function_name}")
    
    code = extract_function(source_file, function_name)
    
    if code:
        # Save as Python file
        output_path = os.path.join(output_dir, f"{key}.py")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n")
            f.write(f"# {description}\n")
            f.write(f"# Function: {function_name}\n\n")
            f.write(code)
        
        # Add to markdown summary
        snippets_md += f"## {title}\n\n"
        snippets_md += f"**Function:** `{function_name}`\n\n"
        snippets_md += f"**Description:** {description}\n\n"
        
        # Include snippet preview (first 50 lines)
        preview_lines = code.split('\n')[:50]
        snippets_md += f"```python\n"
        snippets_md += '\n'.join(preview_lines)
        if len(code.split('\n')) > 50:
            snippets_md += "\n# ... (truncated for preview)\n"
        snippets_md += f"\n```\n\n"
        snippets_md += f"*Full code: `{output_path}`*\n\n"
        snippets_md += "---\n\n"
        
        print(f"  ✅ Saved to: {output_path}")
        extracted_count += 1
    else:
        print(f"  ⚠️  Warning: Function '{function_name}' not found!")
        failed_count += 1
    
    print()

# Save markdown summary
summary_path = os.path.join('report_assets', 'CODE_SNIPPETS.md')
with open(summary_path, 'w', encoding='utf-8') as f:
    f.write(snippets_md)

print("=" * 70)
print(f"✅ Extraction Complete!")
print(f"   Extracted: {extracted_count}/{len(CODE_SECTIONS)}")
if failed_count > 0:
    print(f"   Failed: {failed_count}")
print(f"📄 Summary: {summary_path}")
print("=" * 70)
