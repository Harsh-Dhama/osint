"""
Test Script for Tracker and Username Searcher Modules

This script tests both new modules:
1. Number/Email Tracker
2. Social Media Username Searcher
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api"

# Test credentials (default admin)
USERNAME = "admin"
PASSWORD = "admin123"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def login():
    """Login and get access token"""
    print_section("🔐 AUTHENTICATION TEST")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": USERNAME,
                "password": PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print_success(f"Login successful! Token received")
            return token
        else:
            print_error(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Login error: {e}")
        return None

def test_tracker_module(token):
    """Test the Number/Email Tracker Module"""
    print_section("📞 TRACKER MODULE TESTS")
    
    if not token:
        print_error("No authentication token available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Check credit balance
    print_info("Test 1: Checking credit balance...")
    try:
        response = requests.get(f"{BASE_URL}/tracker/credits/balance", headers=headers)
        if response.status_code == 200:
            data = response.json()
            credits = data.get("current_balance", 0)
            print_success(f"Credit balance retrieved: {credits} credits")
        else:
            print_error(f"Failed to get balance: {response.status_code}")
    except Exception as e:
        print_error(f"Balance check error: {e}")
    
    # Test 2: Get available modules
    print_info("\nTest 2: Getting available modules...")
    try:
        response = requests.get(f"{BASE_URL}/tracker/modules", headers=headers)
        if response.status_code == 200:
            data = response.json()
            modules = data.get("modules", [])
            print_success(f"Retrieved {len(modules)} modules:")
            for module in modules[:5]:  # Show first 5
                display = module.get('display_name', module.get('name', 'Unknown'))
                credits = module.get('credits', 0)
                print(f"   • {display} - {credits} credits")
        else:
            print_error(f"Failed to get modules: {response.status_code}")
    except Exception as e:
        print_error(f"Module retrieval error: {e}")
    
    # Test 3: Get disclaimer
    print_info("\nTest 3: Getting search disclaimer...")
    try:
        response = requests.get(f"{BASE_URL}/tracker/disclaimer", headers=headers)
        if response.status_code == 200:
            data = response.json()
            disclaimer = data.get("content", "")
            print_success(f"Disclaimer retrieved ({len(disclaimer)} characters)")
        else:
            print_error(f"Failed to get disclaimer: {response.status_code}")
    except Exception as e:
        print_error(f"Disclaimer retrieval error: {e}")
    
    # Test 4: Submit a test search (will deduct credits!)
    print_info("\nTest 4: Submitting test search...")
    print_info("⚠️  Note: This will deduct credits from your account!")
    
    search_data = {
        "search_type": "phone",
        "search_value": "+919876543210",
        "case_id": 1,  # Assuming case 1 exists
        "modules": ["truename", "social_media"],  # Valid module names
        "accept_disclaimer": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/tracker/search",
            json=search_data,
            headers=headers
        )
        
        if response.status_code == 201:
            search_result = response.json()
            search_id = search_result.get("search_id")
            print_success(f"Search submitted successfully! ID: {search_id}")
            print_info(f"Status: {search_result.get('status')}")
            print_info(f"Credits used: {search_result.get('credits_used', 0)}")
            
            # Wait and check status
            print_info("\nWaiting 5 seconds to check search status...")
            time.sleep(5)
            
            status_response = requests.get(
                f"{BASE_URL}/tracker/search/{search_id}",
                headers=headers
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print_success(f"Search status: {status_data.get('status')}")
                
                # Try to export PDF
                print_info("\nTest 5: Attempting PDF export...")
                pdf_response = requests.get(
                    f"{BASE_URL}/tracker/search/{search_id}/export/pdf",
                    headers=headers
                )
                
                if pdf_response.status_code == 200:
                    filename = f"test_tracker_report_{search_id}.pdf"
                    with open(filename, 'wb') as f:
                        f.write(pdf_response.content)
                    print_success(f"PDF exported successfully: {filename}")
                else:
                    print_error(f"PDF export failed: {pdf_response.status_code}")
            
        else:
            print_error(f"Search submission failed: {response.status_code} - {response.text}")
    except Exception as e:
        print_error(f"Search submission error: {e}")

def test_username_searcher(token):
    """Test the Username Searcher Module"""
    print_section("🔎 USERNAME SEARCHER TESTS")
    
    if not token:
        print_error("No authentication token available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Get cache statistics
    print_info("Test 1: Getting cache statistics...")
    try:
        response = requests.get(f"{BASE_URL}/username/cache/stats", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print_success("Cache statistics retrieved:")
            print(f"   • Total searches: {stats.get('total_searches', 0)}")
            print(f"   • Valid cache: {stats.get('valid_cache', 0)}")
            print(f"   • Expired cache: {stats.get('expired_cache', 0)}")
            print(f"   • Cache duration: {stats.get('cache_days', 7)} days")
        else:
            print_error(f"Failed to get cache stats: {response.status_code}")
    except Exception as e:
        print_error(f"Cache stats error: {e}")
    
    # Test 2: Search for a username
    print_info("\nTest 2: Searching for username 'github'...")
    print_info("⚠️  This may take 10-30 seconds to check 40+ platforms")
    
    search_data = {
        "username": "github",
        "case_id": None,
        "officer_name": "Test Officer"
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/username/search",
            json=search_data,
            headers=headers
        )
        end_time = time.time()
        
        if response.status_code == 201:
            search_result = response.json()
            search_id = search_result.get("id")
            duration = end_time - start_time
            
            print_success(f"Search completed in {duration:.2f} seconds!")
            print(f"   • Search ID: {search_id}")
            print(f"   • Username: {search_result.get('username')}")
            print(f"   • Platforms checked: {search_result.get('platforms_checked', 0)}")
            print(f"   • Platforms found: {search_result.get('platforms_found', 0)}")
            print(f"   • Status: {search_result.get('status')}")
            
            # Test 3: Get detailed results
            print_info("\nTest 3: Getting detailed platform results...")
            results_response = requests.get(
                f"{BASE_URL}/username/search/{search_id}/results",
                headers=headers
            )
            
            if results_response.status_code == 200:
                results = results_response.json()
                print_success(f"Retrieved {len(results)} platform results:")
                
                # Show top 10 results
                for i, result in enumerate(results[:10], 1):
                    confidence = result.get('confidence_score', 0) * 100
                    print(f"   {i}. {result.get('platform_name')} - {confidence:.0f}% confidence")
                    print(f"      URL: {result.get('platform_url')}")
            
            # Test 4: Export PDF
            print_info("\nTest 4: Exporting PDF report...")
            pdf_response = requests.get(
                f"{BASE_URL}/username/search/{search_id}/export/pdf",
                headers=headers
            )
            
            if pdf_response.status_code == 200:
                filename = f"test_username_report_{search_id}.pdf"
                with open(filename, 'wb') as f:
                    f.write(pdf_response.content)
                print_success(f"PDF exported successfully: {filename}")
            else:
                print_error(f"PDF export failed: {pdf_response.status_code}")
                
        else:
            print_error(f"Search failed: {response.status_code} - {response.text}")
    except Exception as e:
        print_error(f"Username search error: {e}")
    
    # Test 5: Search for another username to test caching
    print_info("\nTest 5: Searching 'github' again to test caching...")
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/username/search",
            json=search_data,
            headers=headers
        )
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 201:
            print_success(f"Cached search completed in {duration:.2f} seconds!")
            if duration < 2:
                print_success("✨ Cache is working! (Search was very fast)")
            else:
                print_info("Cache might not be working (Search took normal time)")
        else:
            print_error(f"Cached search failed: {response.status_code}")
    except Exception as e:
        print_error(f"Cached search error: {e}")

def main():
    """Main test execution"""
    print("\n" + "🚀 "*40)
    print("  OSINT PLATFORM - MODULE TESTING SUITE")
    print("  Testing: Tracker Module + Username Searcher")
    print("  Date: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🚀 "*40)
    
    # Step 1: Login
    token = login()
    
    if not token:
        print_error("\n❌ Cannot proceed without authentication token")
        return
    
    # Step 2: Test Tracker Module
    test_tracker_module(token)
    
    # Step 3: Test Username Searcher
    test_username_searcher(token)
    
    # Summary
    print_section("📊 TEST SUMMARY")
    print_info("All tests completed!")
    print_info("Check the output above for any failures")
    print_info("PDF reports saved in current directory if tests succeeded")
    
    print("\n" + "✅ "*40)
    print("  TESTING COMPLETE!")
    print("✅ "*40 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
