"""
Facial Recognition Module

This module handles facial recognition using local AI models
and reverse image search functionality.
"""

import face_recognition
import cv2
import numpy as np
from typing import List, Dict, Tuple
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup


class FacialRecognition:
    def __init__(self, tolerance: float = 0.6):
        """
        Initialize facial recognition
        
        Args:
            tolerance: Face matching tolerance (0.6 is default, lower is more strict)
        """
        self.tolerance = tolerance
        self.known_faces = []
        self.known_names = []
        
    def load_known_faces(self, database_path: str):
        """
        Load known faces from a directory
        
        Args:
            database_path: Path to directory containing face images
        """
        if not os.path.exists(database_path):
            os.makedirs(database_path, exist_ok=True)
            return
        
        for filename in os.listdir(database_path):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(database_path, filename)
                try:
                    image = face_recognition.load_image_file(image_path)
                    encodings = face_recognition.face_encodings(image)
                    
                    if encodings:
                        self.known_faces.append(encodings[0])
                        self.known_names.append(os.path.splitext(filename)[0])
                except Exception as e:
                    print(f"Error loading {filename}: {str(e)}")
    
    def detect_faces(self, image_path: str) -> List[Dict]:
        """
        Detect faces in an image
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of detected faces with locations
        """
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            faces = []
            for i, (location, encoding) in enumerate(zip(face_locations, face_encodings)):
                faces.append({
                    "face_id": i,
                    "location": location,  # (top, right, bottom, left)
                    "encoding": encoding.tolist()
                })
            
            return faces
        
        except Exception as e:
            print(f"Error detecting faces: {str(e)}")
            return []
    
    def match_faces(self, unknown_image_path: str) -> List[Dict]:
        """
        Match faces in an image against known faces
        
        Args:
            unknown_image_path: Path to image to match
            
        Returns:
            List of matches with confidence scores
        """
        try:
            unknown_image = face_recognition.load_image_file(unknown_image_path)
            unknown_encodings = face_recognition.face_encodings(unknown_image)
            
            if not unknown_encodings:
                return []
            
            matches = []
            
            for unknown_encoding in unknown_encodings:
                # Compare with all known faces
                face_distances = face_recognition.face_distance(
                    self.known_faces, unknown_encoding
                )
                
                for i, distance in enumerate(face_distances):
                    if distance <= self.tolerance:
                        confidence = (1 - distance) * 100
                        matches.append({
                            "name": self.known_names[i],
                            "confidence_score": round(confidence, 2),
                            "distance": round(distance, 4)
                        })
            
            # Sort by confidence
            matches.sort(key=lambda x: x["confidence_score"], reverse=True)
            
            return matches
        
        except Exception as e:
            print(f"Error matching faces: {str(e)}")
            return []
    
    def extract_face(self, image_path: str, output_path: str, face_location: Tuple = None):
        """
        Extract and save a face from an image
        
        Args:
            image_path: Source image path
            output_path: Where to save extracted face
            face_location: Optional specific face location (top, right, bottom, left)
        """
        try:
            image = cv2.imread(image_path)
            
            if face_location:
                top, right, bottom, left = face_location
            else:
                # Detect first face
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_image)
                
                if not face_locations:
                    return False
                
                top, right, bottom, left = face_locations[0]
            
            # Extract face
            face_image = image[top:bottom, left:right]
            
            # Save
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cv2.imwrite(output_path, face_image)
            
            return True
        
        except Exception as e:
            print(f"Error extracting face: {str(e)}")
            return False


class ReverseImageSearch:
    """
    Perform reverse image search on multiple engines
    """
    
    @staticmethod
    def search_google(image_path: str) -> List[Dict]:
        """
        Reverse image search on Google
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of search results
        """
        # Note: This is a simplified implementation
        # In production, you would use Google Custom Search API
        try:
            # Upload to a temporary hosting service or use Google Images upload
            # This is a placeholder implementation
            results = []
            
            # Google reverse image search URL
            search_url = "https://www.google.com/searchbyimage/upload"
            
            with open(image_path, 'rb') as img_file:
                files = {'encoded_image': img_file}
                response = requests.post(search_url, files=files, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Parse results (simplified)
                    for result in soup.find_all('div', class_='g')[:10]:
                        title_elem = result.find('h3')
                        link_elem = result.find('a')
                        
                        if title_elem and link_elem:
                            results.append({
                                "source": "google",
                                "title": title_elem.text,
                                "url": link_elem.get('href'),
                                "engine": "Google"
                            })
            
            return results
        
        except Exception as e:
            print(f"Google search error: {str(e)}")
            return []
    
    @staticmethod
    def search_yandex(image_path: str) -> List[Dict]:
        """
        Reverse image search on Yandex
        """
        # Placeholder - implement Yandex image search
        return []
    
    @staticmethod
    def search_bing(image_path: str) -> List[Dict]:
        """
        Reverse image search on Bing
        """
        # Placeholder - implement Bing image search
        return []
    
    @staticmethod
    def search_all(image_path: str, engines: List[str] = None) -> Dict[str, List[Dict]]:
        """
        Search on multiple engines
        
        Args:
            image_path: Path to image
            engines: List of engines to search (google, yandex, bing)
            
        Returns:
            Dictionary of results by engine
        """
        if engines is None:
            engines = ["google", "yandex", "bing"]
        
        results = {}
        
        if "google" in engines:
            results["google"] = ReverseImageSearch.search_google(image_path)
        
        if "yandex" in engines:
            results["yandex"] = ReverseImageSearch.search_yandex(image_path)
        
        if "bing" in engines:
            results["bing"] = ReverseImageSearch.search_bing(image_path)
        
        return results


# Helper functions
def analyze_face(image_path: str, database_path: str = "data/face_database") -> Dict:
    """
    Complete face analysis pipeline
    
    Args:
        image_path: Path to image to analyze
        database_path: Path to known faces database
        
    Returns:
        Analysis results
    """
    fr = FacialRecognition()
    fr.load_known_faces(database_path)
    
    # Detect faces
    detected_faces = fr.detect_faces(image_path)
    
    # Match faces
    matches = fr.match_faces(image_path)
    
    return {
        "detected_faces": len(detected_faces),
        "matches": matches,
        "timestamp": datetime.utcnow().isoformat()
    }


def perform_reverse_search(image_path: str, engines: List[str] = None) -> Dict:
    """
    Perform reverse image search
    
    Args:
        image_path: Path to image
        engines: List of engines to use
        
    Returns:
        Search results
    """
    results = ReverseImageSearch.search_all(image_path, engines)
    
    return {
        "results": results,
        "total_results": sum(len(v) for v in results.values()),
        "timestamp": datetime.utcnow().isoformat()
    }
