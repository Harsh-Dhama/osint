"""
Debug script to show all images in WhatsApp drawer
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.modules.whatsapp_scraper import WhatsAppScraper

async def debug_drawer_images():
    phone = "916397675890"  # Test number with profile pic
    
    print("\n" + "="*70)
    print(f"  DEBUG: WhatsApp Drawer Images for {phone}")
    print("="*70)
    
    scraper = WhatsAppScraper()
    
    try:
        await scraper.initialize()
        print("✅ Browser initialized")
        
        # Navigate to chat
        url = f"https://web.whatsapp.com/send?phone={phone}"
        print(f"\n📱 Opening chat: {url}")
        await scraper.page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(8)  # Wait for chat to load
        
        # Click header to open drawer
        print("\n🔓 Opening profile drawer...")
        header = await scraper.page.query_selector('header[data-testid="conversation-header"]')
        if header:
            await header.click()
            await asyncio.sleep(5)  # Wait for drawer to load
            print("✅ Drawer opened")
        else:
            print("❌ Could not find header")
            return
        
        # List ALL images in drawer
        print("\n📸 ALL IMAGES IN DRAWER:")
        print("="*70)
        
        images = await scraper.page.evaluate("""
            () => {
                const drawer = document.querySelector('div[data-testid="drawer-right"]');
                if (!drawer) return [];
                
                const imgs = drawer.querySelectorAll('img');
                const result = [];
                
                imgs.forEach((img, index) => {
                    result.push({
                        index: index + 1,
                        src: img.src,
                        alt: img.alt || '',
                        width: img.width,
                        height: img.height,
                        naturalWidth: img.naturalWidth,
                        naturalHeight: img.naturalHeight,
                        className: img.className,
                        isStatic: img.src.includes('/rsrc.php/') || img.src.includes('static.whatsapp.net/rsrc'),
                        isProfilePicServer: img.src.includes('pps.whatsapp.net'),
                        isMediaServer: img.src.includes('mmg.whatsapp.net'),
                    });
                });
                
                return result;
            }
        """)
        
        for img in images:
            print(f"\n[Image #{img['index']}]")
            print(f"  URL: {img['src'][:120]}")
            print(f"  Alt: {img['alt']}")
            print(f"  Size: {img['width']}x{img['height']} (natural: {img['naturalWidth']}x{img['naturalHeight']})")
            print(f"  Class: {img['className'][:50] if img['className'] else 'None'}")
            print(f"  🔍 Analysis:")
            print(f"     Static Resource: {'YES ❌' if img['isStatic'] else 'NO ✓'}")
            print(f"     Profile Pic Server (pps): {'YES ✅' if img['isProfilePicServer'] else 'NO'}")
            print(f"     Media Server (mmg): {'YES ✅' if img['isMediaServer'] else 'NO'}")
            
            # Determine if this should be extracted
            should_extract = (
                (img['isProfilePicServer'] or img['isMediaServer']) 
                and not img['isStatic']
                and img['naturalWidth'] > 32  # Avoid tiny icons
            )
            print(f"     Should Extract: {'YES ✅✅✅' if should_extract else 'NO'}")
        
        print("\n" + "="*70)
        print(f"Total images found: {len(images)}")
        
        profile_pics = [img for img in images if (img['isProfilePicServer'] or img['isMediaServer']) and not img['isStatic']]
        print(f"Valid profile pictures: {len(profile_pics)}")
        
        if profile_pics:
            print("\n✅ CORRECT PROFILE PICTURE:")
            for img in profile_pics:
                print(f"   #{img['index']}: {img['src'][:100]}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔄 Closing...")
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(debug_drawer_images())
