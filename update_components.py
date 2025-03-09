import pandas as pd
from app import app, db
from models import ProductionCell, Component

def update_benchmark_data():
    # Read Excel file
    df = pd.read_excel('attached_assets/Components.xlsx')
    
    with app.app_context():
        try:
            # Delete existing data
            Component.query.delete()
            ProductionCell.query.delete()
            db.session.commit()
            
            # Process each row
            cells = {}
            for _, row in df.iterrows():
                cell_name = row['Cell']
                
                # Create cell if it doesn't exist
                if cell_name not in cells:
                    cell = ProductionCell(
                        name=cell_name,
                        description=f"Production cell for {cell_name}"
                    )
                    db.session.add(cell)
                    db.session.flush()  # Get cell ID
                    cells[cell_name] = cell
                
                # Create component
                component = Component(
                    name=row['Component'],
                    cell_id=cells[cell_name].id,
                    completion_time=float(row['Completion Time (min)']),
                    min_operators=int(row['Min Operators'])
                )
                db.session.add(component)
            
            db.session.commit()
            print("Successfully updated benchmark data")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error updating benchmark data: {str(e)}")
            raise

if __name__ == '__main__':
    update_benchmark_data()
