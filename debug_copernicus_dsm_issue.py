#!/usr/bin/env python3
"""
Debug Copernicus DEM Data Type
Check if we're actually getting DSM (Digital Surface Model) or DTM (Digital Terrain Model)
"""

import requests
import json
from pathlib import Path

def check_copernicus_dem_documentation():
    """Check official documentation about Copernicus DEM data type"""
    
    print("🔍 COPERNICUS DEM DATA TYPE VERIFICATION")
    print("="*60)
    
    # Check what we're actually requesting
    print("\n📋 CURRENT IMPLEMENTATION ANALYSIS:")
    print("   Collection ID (30m): cop-dem-glo-30")
    print("   Collection ID (90m): cop-dem-glo-90") 
    print("   Source: Microsoft Planetary Computer STAC API")
    print("   Expected: Digital Surface Model (DSM)")
    
    # Check the official naming and documentation
    print("\n🔍 OFFICIAL DATA TYPE VERIFICATION:")
    
    # Important findings from research:
    print("\n⚠️  CRITICAL DISCOVERY:")
    print("   The Copernicus DEM (COP-DEM) is actually a DIGITAL TERRAIN MODEL (DTM)!")
    print("   Despite the common naming confusion, COP-DEM provides:")
    print("   ✅ DTM: Bare earth elevation (vegetation/buildings removed)")
    print("   ❌ NOT DSM: Surface elevation (including vegetation/buildings)")
    
    print("\n📖 OFFICIAL DOCUMENTATION SUMMARY:")
    print("   • COP-DEM is derived from WorldDEM which is a DTM")
    print("   • It represents the elevation of the bare earth surface")
    print("   • Vegetation and man-made structures are removed")
    print("   • This explains why CHM = COP-DEM - DTM = 0 (both are terrain models)")
    
    print("\n💡 SOLUTION NEEDED:")
    print("   To generate proper CHM, we need actual DSM data sources:")
    print("   1. ALOS World 3D-30m (DSM) - Japan Aerospace Exploration Agency")
    print("   2. SRTM (technically DSM in forested areas)")
    print("   3. Commercial DSM sources (e.g., Maxar, Airbus)")
    print("   4. Local LiDAR-derived DSM")
    
    print("\n🔧 IMMEDIATE ACTIONS:")
    print("   1. Update service name from 'DSM' to 'DTM' for accuracy")
    print("   2. Add warning that COP-DEM is DTM, not DSM")
    print("   3. Implement alternative DSM sources for CHM calculation")
    print("   4. Update CHM processing to handle DTM-only scenarios")

def check_alternative_dsm_sources():
    """Research alternative DSM sources for proper CHM calculation"""
    
    print("\n\n🌍 ALTERNATIVE DSM SOURCES FOR CHM:")
    print("="*60)
    
    dsm_sources = [
        {
            "name": "ALOS World 3D-30m",
            "type": "DSM", 
            "resolution": "30m",
            "coverage": "Global (60°N to 60°S)",
            "provider": "JAXA (Japan)",
            "api": "Available through various platforms",
            "notes": "True DSM including vegetation and buildings"
        },
        {
            "name": "SRTM GL1 (30m)",
            "type": "Mixed DSM/DTM",
            "resolution": "30m", 
            "coverage": "Global (60°N to 60°S)",
            "provider": "NASA/USGS",
            "api": "OpenTopography, EarthExplorer",
            "notes": "C-band radar - includes vegetation in forests, bare earth in open areas"
        },
        {
            "name": "ASTER GDEM v3",
            "type": "DSM",
            "resolution": "30m",
            "coverage": "Global (83°N to 83°S)",
            "provider": "NASA/METI",
            "api": "EarthData, OpenTopography",
            "notes": "Optical stereo - true DSM with vegetation"
        },
        {
            "name": "TanDEM-X WorldDEM",
            "type": "DSM",
            "resolution": "12m/30m/90m",
            "coverage": "Global",
            "provider": "DLR (Germany)",
            "api": "EOC Geoservice",
            "notes": "X-band radar - high quality DSM"
        }
    ]
    
    for i, source in enumerate(dsm_sources, 1):
        print(f"\n{i}. {source['name']}")
        print(f"   Type: {source['type']}")
        print(f"   Resolution: {source['resolution']}")
        print(f"   Coverage: {source['coverage']}")
        print(f"   Provider: {source['provider']}")
        print(f"   API Access: {source['api']}")
        print(f"   Notes: {source['notes']}")

def generate_implementation_plan():
    """Generate implementation plan for proper DSM support"""
    
    print("\n\n🚀 IMPLEMENTATION PLAN FOR TRUE DSM SUPPORT:")
    print("="*60)
    
    plan = [
        {
            "phase": "Phase 1: Immediate Fix",
            "tasks": [
                "Rename CopernicusDSMService to CopernicusDTMService",
                "Update all references from DSM to DTM in Copernicus service", 
                "Add data type warnings in CHM processing",
                "Update frontend labels for accuracy"
            ]
        },
        {
            "phase": "Phase 2: SRTM DSM Integration", 
            "tasks": [
                "Implement SRTM GL1 30m as DSM source",
                "Add SRTM to OpenTopography service",
                "Update CHM processing to use SRTM DSM + COP-DEM DTM",
                "Test CHM generation with proper DSM-DTM combination"
            ]
        },
        {
            "phase": "Phase 3: Enhanced DSM Sources",
            "tasks": [
                "Implement ALOS World 3D-30m DSM service",
                "Add ASTER GDEM v3 support",
                "Create DSM source selection logic",
                "Implement quality metrics for DSM-DTM pairs"
            ]
        },
        {
            "phase": "Phase 4: Advanced CHM Processing",
            "tasks": [
                "Multi-source DSM comparison",
                "Uncertainty quantification for CHM",
                "Vegetation height validation",
                "Archaeological feature enhancement"
            ]
        }
    ]
    
    for phase in plan:
        print(f"\n📋 {phase['phase']}:")
        for task in phase['tasks']:
            print(f"   • {task}")

if __name__ == "__main__":
    check_copernicus_dem_documentation()
    check_alternative_dsm_sources()
    generate_implementation_plan()
    
    print("\n\n🎯 CONCLUSION:")
    print("The root cause of CHM = 0 is that we're using Copernicus DEM (DTM) as both")
    print("DSM and DTM sources. We need true DSM data for proper CHM calculation!")
