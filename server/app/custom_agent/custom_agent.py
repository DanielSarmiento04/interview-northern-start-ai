import json
import pandas as pd
from . import (
    get_rent_data as _get_rent_data,
    get_sale_data as _get_sale_data
)
from agents import Agent, WebSearchTool, function_tool

STYLE_INSTRUCTIONS = "Use a conversational tone and write in a chat style without formal formatting or lists and do not use any emojis."


@function_tool
def get_rent_data() -> str:
    '''
        Function to recover Airbnb rental data (short-term rentals).
        Returns a sample of Airbnb listings with summary statistics.
    '''
    try:
        data = _get_rent_data()
        
        # Get basic info about the dataset
        total_rows = len(data)
        
        # Clean price column (remove $ and spaces, convert to numeric)
        if 'price' in data.columns:
            data['price_numeric'] = data['price'].str.replace('$', '').str.replace(' ', '').str.replace(',', '')
            data['price_numeric'] = pd.to_numeric(data['price_numeric'], errors='coerce')
        
        # Sample data for analysis (max 50 records to avoid token limits)
        sample_size = min(50, total_rows)
        sample_data = data.sample(n=sample_size, random_state=42)
        
        # Get neighborhood distribution
        neighborhood_stats = data['neighbourhood group'].value_counts().head(10).to_dict() if 'neighbourhood group' in data.columns else {}
        room_type_stats = data['room type'].value_counts().to_dict() if 'room type' in data.columns else {}
        
        # Generate summary statistics
        summary = {
            "dataset_info": {
                "total_listings": total_rows,
                "sample_size": sample_size,
                "data_type": "Airbnb Short-term Rentals",
                "columns": list(data.columns)
            },
            "market_insights": {
                "top_neighborhoods": neighborhood_stats,
                "room_types": room_type_stats
            },
            "sample_listings": sample_data[['NAME', 'neighbourhood group', 'neighbourhood', 'room type', 'price', 'minimum nights', 'number of reviews']].to_dict('records')
        }
        
        # Add price statistics if available
        if 'price_numeric' in data.columns:
            price_stats = data['price_numeric'].describe()
            summary["price_statistics"] = {
                "mean_nightly_rate": float(price_stats['mean']) if not pd.isna(price_stats['mean']) else None,
                "median_nightly_rate": float(data['price_numeric'].median()) if not pd.isna(data['price_numeric'].median()) else None,
                "min_nightly_rate": float(price_stats['min']) if not pd.isna(price_stats['min']) else None,
                "max_nightly_rate": float(price_stats['max']) if not pd.isna(price_stats['max']) else None,
                "std_deviation": float(price_stats['std']) if not pd.isna(price_stats['std']) else None
            }
        
        return json.dumps(summary, default=str)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to load Airbnb rental data: {str(e)}"})

@function_tool
def search_rent_by_price_range(min_price: int = 0, max_price: int = 10000) -> str:
    '''
        Search Airbnb listings within a specific nightly price range.
        Args:
            min_price: Minimum nightly price filter
            max_price: Maximum nightly price filter
    '''
    try:
        data = _get_rent_data()
        
        # Clean price column
        if 'price' in data.columns:
            data['price_numeric'] = data['price'].str.replace('$', '').str.replace(' ', '').str.replace(',', '')
            data['price_numeric'] = pd.to_numeric(data['price_numeric'], errors='coerce')
            
            # Filter by price range
            filtered_data = data[
                (data['price_numeric'] >= min_price) & 
                (data['price_numeric'] <= max_price)
            ]
            
            # Sample if too many results
            sample_size = min(30, len(filtered_data))
            if len(filtered_data) > sample_size:
                filtered_data = filtered_data.sample(n=sample_size, random_state=42)
            
            result = {
                "total_matches": len(data[(data['price_numeric'] >= min_price) & (data['price_numeric'] <= max_price)]),
                "sample_size": len(filtered_data),
                "price_range": f"${min_price} - ${max_price} per night",
                "listings": filtered_data[['NAME', 'neighbourhood group', 'neighbourhood', 'room type', 'price', 'minimum nights', 'number of reviews']].to_dict('records')
            }
            
            return json.dumps(result, default=str)
        else:
            return json.dumps({"error": "Price column not found in the dataset"})
            
    except Exception as e:
        return json.dumps({"error": f"Failed to search Airbnb listings: {str(e)}"})

@function_tool
def search_rent_by_neighborhood(neighborhood: str = "") -> str:
    '''
        Search Airbnb listings by neighborhood or area.
        Args:
            neighborhood: Neighborhood name to search for
    '''
    try:
        data = _get_rent_data()
        
        if not neighborhood:
            # Return available neighborhoods
            neighborhoods = data['neighbourhood group'].value_counts().head(20).to_dict() if 'neighbourhood group' in data.columns else {}
            return json.dumps({
                "available_neighborhoods": neighborhoods,
                "message": "Specify a neighborhood name to search for listings"
            })
        
        # Filter by neighborhood (case insensitive)
        if 'neighbourhood group' in data.columns:
            filtered_data = data[data['neighbourhood group'].str.contains(neighborhood, case=False, na=False)]
        elif 'neighbourhood' in data.columns:
            filtered_data = data[data['neighbourhood'].str.contains(neighborhood, case=False, na=False)]
        else:
            return json.dumps({"error": "Neighborhood columns not found"})
        
        # Sample if too many results
        sample_size = min(30, len(filtered_data))
        if len(filtered_data) > sample_size:
            filtered_data = filtered_data.sample(n=sample_size, random_state=42)
        
        result = {
            "total_matches": len(filtered_data),
            "sample_size": len(filtered_data),
            "neighborhood": neighborhood,
            "listings": filtered_data[['NAME', 'neighbourhood group', 'neighbourhood', 'room type', 'price', 'minimum nights', 'number of reviews']].to_dict('records')
        }
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to search by neighborhood: {str(e)}"})

@function_tool
def get_sale_data() -> str:
    '''
        Function to recover property sales data from Perth real estate market.
        Returns a sample of property sales with summary statistics.
    '''
    try:
        data = _get_sale_data()
        
        # Get basic info about the dataset
        total_rows = len(data)
        
        # Sample data for analysis (max 50 records to avoid token limits)
        sample_size = min(50, total_rows)
        sample_data = data.sample(n=sample_size, random_state=42)
        
        # Get suburb distribution
        suburb_stats = data['SUBURB'].value_counts().head(10).to_dict() if 'SUBURB' in data.columns else {}
        
        # Generate summary
        summary = {
            "dataset_info": {
                "total_sales": total_rows,
                "sample_size": sample_size,
                "data_type": "Perth Property Sales",
                "columns": list(data.columns)
            },
            "market_insights": {
                "top_suburbs": suburb_stats,
                "date_range": {
                    "earliest": str(data['DATE_SOLD'].min()) if 'DATE_SOLD' in data.columns else None,
                    "latest": str(data['DATE_SOLD'].max()) if 'DATE_SOLD' in data.columns else None
                }
            },
            "sample_properties": sample_data[['ADDRESS', 'SUBURB', 'PRICE', 'BEDROOMS', 'BATHROOMS', 'GARAGE', 'FLOOR_AREA', 'DATE_SOLD']].to_dict('records')
        }
        
        # Add price statistics if available
        if 'PRICE' in data.columns:
            price_stats = data['PRICE'].describe()
            summary["price_statistics"] = {
                "mean_sale_price": float(price_stats['mean']) if not pd.isna(price_stats['mean']) else None,
                "median_sale_price": float(data['PRICE'].median()) if not pd.isna(data['PRICE'].median()) else None,
                "min_sale_price": float(price_stats['min']) if not pd.isna(price_stats['min']) else None,
                "max_sale_price": float(price_stats['max']) if not pd.isna(price_stats['max']) else None,
                "std_deviation": float(price_stats['std']) if not pd.isna(price_stats['std']) else None
            }
        
        return json.dumps(summary, default=str)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to load property sales data: {str(e)}"})

@function_tool
def search_sales_by_price_range(min_price: int = 0, max_price: int = 10000000) -> str:
    '''
        Search property sales within a specific price range.
        Args:
            min_price: Minimum sale price filter
            max_price: Maximum sale price filter
    '''
    try:
        data = _get_sale_data()
        
        if 'PRICE' in data.columns:
            # Filter by price range
            filtered_data = data[
                (data['PRICE'] >= min_price) & 
                (data['PRICE'] <= max_price)
            ]
            
            # Sample if too many results
            sample_size = min(30, len(filtered_data))
            if len(filtered_data) > sample_size:
                filtered_data = filtered_data.sample(n=sample_size, random_state=42)
            
            result = {
                "total_matches": len(data[(data['PRICE'] >= min_price) & (data['PRICE'] <= max_price)]),
                "sample_size": len(filtered_data),
                "price_range": f"${min_price:,} - ${max_price:,}",
                "properties": filtered_data[['ADDRESS', 'SUBURB', 'PRICE', 'BEDROOMS', 'BATHROOMS', 'GARAGE', 'FLOOR_AREA', 'DATE_SOLD']].to_dict('records')
            }
            
            return json.dumps(result, default=str)
        else:
            return json.dumps({"error": "Price column not found in the dataset"})
            
    except Exception as e:
        return json.dumps({"error": f"Failed to search property sales: {str(e)}"})

@function_tool
def search_sales_by_suburb(suburb: str = "") -> str:
    '''
        Search property sales by suburb.
        Args:
            suburb: Suburb name to search for
    '''
    try:
        data = _get_sale_data()
        
        if not suburb:
            # Return available suburbs
            suburbs = data['SUBURB'].value_counts().head(20).to_dict() if 'SUBURB' in data.columns else {}
            return json.dumps({
                "available_suburbs": suburbs,
                "message": "Specify a suburb name to search for property sales"
            })
        
        # Filter by suburb (case insensitive)
        if 'SUBURB' in data.columns:
            filtered_data = data[data['SUBURB'].str.contains(suburb, case=False, na=False)]
        else:
            return json.dumps({"error": "Suburb column not found"})
        
        # Sample if too many results
        sample_size = min(30, len(filtered_data))
        if len(filtered_data) > sample_size:
            filtered_data = filtered_data.sample(n=sample_size, random_state=42)
        
        # Calculate suburb statistics
        suburb_stats = {
            "average_price": float(filtered_data['PRICE'].mean()) if 'PRICE' in filtered_data.columns and not filtered_data.empty else None,
            "median_price": float(filtered_data['PRICE'].median()) if 'PRICE' in filtered_data.columns and not filtered_data.empty else None,
            "total_sales": len(filtered_data)
        }
        
        result = {
            "suburb": suburb,
            "statistics": suburb_stats,
            "sample_size": len(filtered_data),
            "properties": filtered_data[['ADDRESS', 'SUBURB', 'PRICE', 'BEDROOMS', 'BATHROOMS', 'GARAGE', 'FLOOR_AREA', 'DATE_SOLD']].to_dict('records')
        }
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to search by suburb: {str(e)}"})


# declare the agents
rent_support_agent = Agent(
    name="Airbnb Rental Support Agent",
    instructions=f"You are an Airbnb rental support assistant specializing in short-term rental listings. You have access to a comprehensive dataset of Airbnb properties with information about nightly rates, neighborhoods, room types, and guest reviews. Help users find suitable short-term rentals, analyze pricing trends, and provide market insights for vacation rentals and temporary accommodations. {STYLE_INSTRUCTIONS}",
    model="gpt-4o-mini",
    tools=[get_rent_data, search_rent_by_price_range, search_rent_by_neighborhood],
)

sale_support_agent = Agent(
    name="Property Sales Support Agent", 
    instructions=f"You are a property sales support assistant specializing in Perth real estate market data. You have access to comprehensive property sales records including prices, locations, property features, and sale dates. Help users analyze property values, market trends, and find properties that match their criteria. Provide insights about different suburbs, price ranges, and property characteristics. {STYLE_INSTRUCTIONS}",
    model="gpt-4o-mini",
    tools=[get_sale_data, search_sales_by_price_range, search_sales_by_suburb],
)