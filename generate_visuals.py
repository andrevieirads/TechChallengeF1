import json
import os
import uuid
import shutil

def create_card_visual(measure_table, measure_name, title, x, y, width, height, z=1000):
    vis_name = str(uuid.uuid4()).replace('-', '')[:20]
    visual_json = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.6.0/schema.json",
        "name": vis_name,
        "position": {
            "x": x,
            "y": y,
            "z": z,
            "width": width,
            "height": height
        },
        "visual": {
            "visualType": "card",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [
                            {
                                "field": {
                                    "Measure": {
                                        "Expression": {
                                            "SourceRef": {
                                                "Entity": measure_table
                                            }
                                        },
                                        "Property": measure_name
                                    }
                                },
                                "queryRef": f"{measure_table}.{measure_name}"
                            }
                        ]
                    }
                }
            },
            "objects": {
                "title": [
                    {
                        "properties": {
                            "show": {
                                "expr": {
                                    "Literal": {
                                        "Value": "true"
                                    }
                                }
                            },
                            "text": {
                                "expr": {
                                    "Literal": {
                                        "Value": f"'{title}'"
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
    }
    return vis_name, visual_json


def create_column_chart(measure_table, measure_name, x, y, width, height, title, z=2000):
    vis_name = str(uuid.uuid4()).replace('-', '')[:20]
    visual_json = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.6.0/schema.json",
        "name": vis_name,
        "position": {"x": x, "y": y, "z": z, "width": width, "height": height},
        "visual": {
            "visualType": "columnChart",
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [
                            {
                                "field": {
                                    "Column": {
                                        "Expression": {
                                            "SourceRef": {
                                                "Entity": "LocalDateTable_8ba65c18-652d-4b6b-a7bb-e62f1ef6dbb3"
                                            }
                                        },
                                        "Property": "Mês"
                                    }
                                },
                                "queryRef": "LocalDateTable_8ba65c18-652d-4b6b-a7bb-e62f1ef6dbb3.Mês"
                            }
                        ]
                    },
                    "Y": {
                        "projections": [
                            {
                                "field": {
                                    "Measure": {
                                        "Expression": {
                                            "SourceRef": {
                                                "Entity": measure_table
                                            }
                                        },
                                        "Property": measure_name
                                    }
                                },
                                "queryRef": f"{measure_table}.{measure_name}"
                            }
                        ]
                    }
                }
            },
            "objects": {
                "title": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "text": {"expr": {"Literal": {"Value": f"'{title}'"}}}
                        }
                    }
                ]
            }
        }
    }
    return vis_name, visual_json

def create_bar_chart(measure_table, measure_name, category_table, category_column, x, y, width, height, title, z=2000):
    vis_name = str(uuid.uuid4()).replace('-', '')[:20]
    visual_json = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.6.0/schema.json",
        "name": vis_name,
        "position": {"x": x, "y": y, "z": z, "width": width, "height": height},
        "visual": {
            "visualType": "barChart",
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [
                            {
                                "field": {
                                    "Column": {
                                        "Expression": {
                                            "SourceRef": {
                                                "Entity": category_table
                                            }
                                        },
                                        "Property": category_column
                                    }
                                },
                                "queryRef": f"{category_table}.{category_column}"
                            }
                        ]
                    },
                    "Y": {
                        "projections": [
                            {
                                "field": {
                                    "Measure": {
                                        "Expression": {
                                            "SourceRef": {
                                                "Entity": measure_table
                                            }
                                        },
                                        "Property": measure_name
                                    }
                                },
                                "queryRef": f"{measure_table}.{measure_name}"
                            }
                        ]
                    }
                }
            },
            "objects": {
                "title": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "text": {"expr": {"Literal": {"Value": f"'{title}'"}}}
                        }
                    }
                ]
            }
        }
    }
    return vis_name, visual_json


def main():
    pages_dir = r"PowerBI\Report Tech Challenge F1.Report\definition\pages"
    
    # Encontrar a página principal (normalmente a primeira)
    page_id = None
    for folder_name in os.listdir(pages_dir):
        if os.path.isdir(os.path.join(pages_dir, folder_name)) and folder_name != "pages.json":
            page_id = folder_name
            break
            
    if not page_id:
        print("Page not found")
        return
        
    visuals_dir = os.path.join(pages_dir, page_id, "visuals")
    os.makedirs(visuals_dir, exist_ok=True)
    
    # Limpar visuais antigos
    for f in os.listdir(visuals_dir):
        path = os.path.join(visuals_dir, f)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        
    visuals = [
        # Cards Topo
        create_card_visual("olist_order_items_dataset", "Total Revenue", "Receita Total", 20, 20, 150, 80),
        create_card_visual("olist_order_items_dataset", "Total Items Sold", "Total Itens", 180, 20, 150, 80),
        create_card_visual("olist_orders_dataset", "Total Orders", "Total Pedidos", 340, 20, 150, 80),
        create_card_visual("olist_orders_dataset", "Avg Delivery Days", "Média Dias Entrega", 500, 20, 150, 80),
        create_card_visual("olist_orders_dataset", "On-Time Delivery %", "% Entregue no Prazo", 660, 20, 150, 80),
        create_card_visual("olist_order_reviews_dataset", "Average Review Score", "Nota Média (Estrelas)", 820, 20, 150, 80),
        create_card_visual("olist_order_reviews_dataset", "% 5-Star Reviews", "% 5-Estrelas", 980, 20, 150, 80),
        
        # Charts Embaixo
        create_column_chart("olist_order_items_dataset", "Total Revenue", 20, 120, 500, 300, "Receita por Mês"),
        create_bar_chart("olist_orders_dataset", "Avg Delivery Days", "olist_geolocation_dataset", "geolocation_state", 540, 120, 500, 300, "Dias de Entrega por Estado"),
        create_column_chart("olist_orders_dataset", "Total Orders", 20, 440, 500, 250, "Total de Pedidos por Mês"),
        create_bar_chart("olist_order_reviews_dataset", "Average Review Score", "product_category_name_translation", "product_category_name_english", 540, 440, 500, 250, "Nota Média por Categoria (Inglês)")
    ]
    
    for name, vis_json in visuals:
        vis_folder = os.path.join(visuals_dir, name)
        os.makedirs(vis_folder, exist_ok=True)
        with open(os.path.join(vis_folder, "visual.json"), "w", encoding="utf-8") as f:
            json.dump(vis_json, f, indent=2, ensure_ascii=False)
            
    print(f"Criados {len(visuals)} visuais com sucesso.")
    
if __name__ == "__main__":
    main()
