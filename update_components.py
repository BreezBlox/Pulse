import pandas as pd
from app import app, db
from models import ProductionCell, Component, JobComponent

def update_benchmark_data():
    # Read Excel file
    df = pd.read_excel('attached_assets/Components.xlsx')

    print("Excel columns:", df.columns.tolist())  # Debug: print column names

    with app.app_context():
        try:
            # Delete existing data in correct order
            JobComponent.query.delete()  # Delete job components first
            Component.query.delete()
            ProductionCell.query.delete()
            db.session.commit()

            # Process each row
            cells = {}
            for _, row in df.iterrows():
                print("Processing row:", row.to_dict())  # Debug: print row data
                cell_name = f"Cell {row['Cell']}"  # Convert number to "Cell X" format

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
                    completion_time=float(row['Time to complete']) * 60,  # Convert hours to minutes
                    min_operators=int(row['Using how many operators']),
                    is_optional=row['Standard(s) or Optional(o)'].upper() == 'O'  # Set is_optional based on the column
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