#!/usr/bin/env python3
"""
Service Layer Validation

Quick validation script to ensure all services are properly implemented
and can be imported and instantiated without errors.
"""

import asyncio
import sys
from typing import List, Tuple

def validate_imports() -> Tuple[bool, List[str]]:
    """Validate that all services can be imported"""
    print("🔍 Validating service imports...")
    errors = []
    
    try:
        # Test individual service imports
        from app.api.cache_service import CacheService
        from app.api.data_acquisition_service import DataAcquisitionService
        from app.api.lidar_acquisition_service import LidarAcquisitionService
        from app.api.pipeline_service import PipelineService
        from app.api.chat_service import ChatService
        from app.api.core_service import CoreService
        print("   ✅ Individual service imports successful")
    except Exception as e:
        errors.append(f"Individual service imports failed: {e}")
    
    try:
        # Test bulk import from main module
        from app.api import (
            CacheService, DataAcquisitionService, LidarAcquisitionService,
            PipelineService, ChatService, CoreService, ServiceFactory
        )
        print("   ✅ Bulk service imports successful")
    except Exception as e:
        errors.append(f"Bulk service imports failed: {e}")
    
    try:
        # Test factory imports
        from app.api import default_factory, cache, data_acquisition, lidar_acquisition
        from app.api import pipelines, chat, core
        print("   ✅ Factory and convenience function imports successful")
    except Exception as e:
        errors.append(f"Factory imports failed: {e}")
    
    return len(errors) == 0, errors


def validate_instantiation() -> Tuple[bool, List[str]]:
    """Validate that all services can be instantiated"""
    print("\n🏗️ Validating service instantiation...")
    errors = []
    
    try:
        from app.api import (
            CacheService, DataAcquisitionService, LidarAcquisitionService,
            PipelineService, ChatService, CoreService
        )
        
        # Test service instantiation
        services = [
            ("CacheService", CacheService),
            ("DataAcquisitionService", DataAcquisitionService),
            ("LidarAcquisitionService", LidarAcquisitionService),
            ("PipelineService", PipelineService),
            ("ChatService", ChatService),
            ("CoreService", CoreService)
        ]
        
        instantiated_services = []
        for name, service_class in services:
            try:
                service = service_class("http://localhost:8000")
                instantiated_services.append((name, service))
                print(f"   ✅ {name} instantiated successfully")
            except Exception as e:
                errors.append(f"{name} instantiation failed: {e}")
        
        # Clean up instantiated services
        for name, service in instantiated_services:
            try:
                if hasattr(service, 'close_sync'):
                    service.close_sync()
            except:
                pass  # Ignore cleanup errors
                
    except Exception as e:
        errors.append(f"Service instantiation test failed: {e}")
    
    return len(errors) == 0, errors


def validate_factory() -> Tuple[bool, List[str]]:
    """Validate that the service factory works correctly"""
    print("\n🏭 Validating service factory...")
    errors = []
    
    try:
        from app.api import ServiceFactory, default_factory
        
        # Test custom factory
        factory = ServiceFactory("http://localhost:8000")
        
        # Test all factory methods
        factory_methods = [
            ("get_cache_service", factory.get_cache_service),
            ("get_data_acquisition_service", factory.get_data_acquisition_service),
            ("get_lidar_acquisition_service", factory.get_lidar_acquisition_service),
            ("get_pipeline_service", factory.get_pipeline_service),
            ("get_chat_service", factory.get_chat_service),
            ("get_core_service", factory.get_core_service)
        ]
        
        for method_name, method in factory_methods:
            try:
                service = method()
                print(f"   ✅ {method_name}() successful")
            except Exception as e:
                errors.append(f"Factory method {method_name} failed: {e}")
        
        # Test default factory
        try:
            default_cache = default_factory.get_cache_service()
            default_core = default_factory.get_core_service()
            print("   ✅ Default factory access successful")
        except Exception as e:
            errors.append(f"Default factory access failed: {e}")
        
        # Test convenience aliases
        try:
            from app.api import cache, data_acquisition, chat, core
            cache_service = cache()
            data_acq_service = data_acquisition()
            chat_service = chat()
            core_service = core()
            print("   ✅ Convenience aliases successful")
        except Exception as e:
            errors.append(f"Convenience aliases failed: {e}")
        
        # Cleanup factory
        try:
            factory.close_all_sync()
        except:
            pass
            
    except Exception as e:
        errors.append(f"Factory validation failed: {e}")
    
    return len(errors) == 0, errors


async def validate_async_operations() -> Tuple[bool, List[str]]:
    """Validate that async operations work correctly"""
    print("\n⚡ Validating async operations...")
    errors = []
    
    try:
        from app.api import CacheService, CoreService
        
        # Test async context manager
        try:
            cache_service = CacheService("http://localhost:8000")
            # Just test that we can get a session without actual network calls
            session = await cache_service._get_session()
            if session is not None:
                print("   ✅ Async session creation successful")
            await cache_service.close()
        except Exception as e:
            errors.append(f"Async session creation failed: {e}")
        
        # Test factory async context manager
        try:
            from app.api import ServiceFactory
            async with ServiceFactory("http://localhost:8000") as factory:
                cache = factory.get_cache_service()
                core = factory.get_core_service()
                print("   ✅ Async factory context manager successful")
        except Exception as e:
            errors.append(f"Async factory context manager failed: {e}")
            
    except Exception as e:
        errors.append(f"Async operations validation failed: {e}")
    
    return len(errors) == 0, errors


async def main():
    """Run all validation tests"""
    print("🔬 SERVICE LAYER VALIDATION")
    print("=" * 60)
    print("Validating all 6 newly implemented services...")
    print("=" * 60)
    
    all_passed = True
    all_errors = []
    
    # Run validation tests
    tests = [
        ("Import Validation", validate_imports),
        ("Instantiation Validation", validate_instantiation),
        ("Factory Validation", validate_factory),
    ]
    
    for test_name, test_func in tests:
        passed, errors = test_func()
        if not passed:
            all_passed = False
            all_errors.extend(errors)
            print(f"   ❌ {test_name} FAILED")
            for error in errors:
                print(f"      - {error}")
        else:
            print(f"   ✅ {test_name} PASSED")
    
    # Run async validation
    passed, errors = await validate_async_operations()
    if not passed:
        all_passed = False
        all_errors.extend(errors)
        print(f"   ❌ Async Validation FAILED")
        for error in errors:
            print(f"      - {error}")
    else:
        print(f"   ✅ Async Validation PASSED")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✅ Service layer is properly implemented and ready for use.")
        print("\nServices successfully validated:")
        print("   • CacheService")
        print("   • DataAcquisitionService") 
        print("   • LidarAcquisitionService")
        print("   • PipelineService")
        print("   • ChatService")
        print("   • CoreService")
        print("   • ServiceFactory")
        print("   • Convenience aliases")
        print("   • Async operations")
        return 0
    else:
        print("❌ VALIDATION FAILED!")
        print(f"Found {len(all_errors)} errors:")
        for error in all_errors:
            print(f"   - {error}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
