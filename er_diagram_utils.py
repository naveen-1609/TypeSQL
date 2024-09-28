# er_diagram_utils.py
import graphviz

def generate_er_diagram(schema):
    """Generate an ER diagram using the provided schema."""
    er_diagram = graphviz.Digraph(format='png')
    tables = schema.split(";")  # Split schema by tables

    for table in tables:
        table = table.strip()
        if not table:
            continue
        
        # Extract table name and fields
        table_name = table.split('(')[0].replace("CREATE TABLE", "").strip()
        fields = table.split('(')[1].replace(")", "").strip().split(',')
        
        # Add table node
        er_diagram.node(table_name, table_name)
        
        # Add fields as part of the table node and relations
        for field in fields:
            field = field.strip()
            if "FOREIGN KEY" in field:
                # Handle foreign key relationships
                foreign_key_info = field.split("REFERENCES")
                fk_field = foreign_key_info[0].replace("FOREIGN KEY", "").strip().replace("(", "").replace(")", "")
                referenced_table = foreign_key_info[1].split("(")[0].strip()
                er_diagram.edge(table_name, referenced_table, label=f"{fk_field} → {referenced_table}")
            else:
                er_diagram.node(f"{table_name}_{field}", field, shape='box')
                er_diagram.edge(f"{table_name}", f"{table_name}_{field}")
    
    return er_diagram
