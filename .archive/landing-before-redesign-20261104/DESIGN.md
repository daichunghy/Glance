---
version: 1.2.0
name: Glance-Apple-Pro-Design-System
description: The official design system for Glance, integrating Apple's Liquid Retina XDR aesthetic, Zero Chrome discipline, alternating light/dark tile canvas rhythm, SF Pro typography with Calibri priority for Vietnamese text, and the signature Action Blue (#0066cc / #2997ff) interaction model.

colors:
  # Interactive Actions
  primary: "#0066cc"                # Apple Action Blue (Light Canvas)
  primary-focus: "#0071e3"          # Focus & Hover Blue
  primary-on-dark: "#2997ff"        # Sky Link Blue (Dark Canvas & Tiles)
  on-primary: "#ffffff"
  
  # Neutrals & Inks
  ink: "#1d1d1f"                    # Primary near-black body ink on light surfaces
  ink-muted-80: "#333333"           # Secondary text on light surfaces
  ink-muted-48: "#7a7a7a"           # Tertiary text / metadata
  body-on-dark: "#ffffff"
  body-muted-dark: "#a1a1a6"
  
  # Canvas & Alternating Surfaces
  canvas-black: "#000000"           # Obsidian Hero Black
  canvas-parchment: "#f5f5f7"       # Apple Iconic Light Parchment
  canvas-pearl: "#ffffff"           # Pure White Studio Surface
  surface-tile-dark: "#161618"      # Charcoal Pro Tile
  surface-glass-dark: "rgba(255, 255, 255, 0.04)"
  
  # Hairline Borders (Zero-Chrome)
  hairline-light: "rgba(0, 0, 0, 0.08)"
  hairline-dark: "rgba(255, 255, 255, 0.12)"
  
  # Pro Glow & Accents
  pro-sapphire: "#2997ff"
  pro-electric: "#38bdf8"
  pro-cyan: "#00f2fe"

typography:
  font-family-body: "'Calibri', -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Roboto, sans-serif"
  font-family-display: "'Calibri', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif"
  font-size-body: "11pt"
  hero-display-tracking: "-0.03em"
  heading-tracking: "-0.025em"

rounded:
  pill: "9999px"                    # Primary CTA Buttons, Search Capsule, Badges
  card-lg: "20px"                   # Feature Cards & Bento Grids
  card-md: "14px"                   # Utility Boxes
  control-sm: "8px"                 # Segmented controls

shadows:
  product-resting: "0 35px 80px rgba(0, 0, 0, 0.85)" # ONLY for MacBook Pro Hardware Showcase
  none: "none"                      # UI Cards & Buttons have zero drop-shadow
---

# Glance Design System Specification (DESIGN.md)

Tài liệu đặc tả kiến trúc thị giác và quy chuẩn giao diện cho Glance, lấy cảm hứng trực tiếp từ trang màn hình Liquid Retina XDR của Apple và bộ tiêu chuẩn DesignMD. Chi tiết toàn diện xem tại [DESIGN_REFERENCES.md](file:///Users/macos/Desktop/Glance/DESIGN_REFERENCES.md).

## 0. Danh Sách Website Tham Khảo Thiết Kế Cho AI
Mọi mô hình AI và nhà phát triển cần tham chiếu các website chuẩn hóa sau đây trước khi triển khai thiết kế:
1. **Kiến trúc UX & Tính năng Glance gốc:** [https://www.tryglance.app/#design](https://www.tryglance.app/#design) — Tham khảo cách bố trí các thẻ tính năng Directional Blur, Presence Guard và on-device privacy.
2. **Thẩm mỹ Apple Liquid Retina XDR:** [https://www.apple.com/vn/macbook-pro/proled-xdr-display/](https://www.apple.com/vn/macbook-pro/proled-xdr-display/) — Chuẩn sắc xanh Sapphire / Apple Action Blue (`#0066cc` / `#0071e3` / `#2997ff`) và nhịp điệu Canvas luân phiên (Obsidian `#000000` ➔ Parchment `#f5f5f7` ➔ Space Black).
3. **Quy chuẩn Design Tokens Apple:** [https://www.designmd.co/d/apple](https://www.designmd.co/d/apple) — Nguyên tắc Zero-Chrome (viền hairline 1px thay vì drop shadow), nút con nhộng `border-radius: 9999px`.
4. **Benchmark Video Launch Sản Phẩm:** [https://www.youtube.com/watch?v=awUYikrGsKk](https://www.youtube.com/watch?v=awUYikrGsKk) — Benchmark video SaaS cao cấp chuẩn Numtera (xem chi tiết tại [LAUNCH_VIDEO_BENCHMARK.md](file:///Users/macos/Desktop/Glance/LAUNCH_VIDEO_BENCHMARK.md)).
5. **Tài liệu Cổng Thanh Toán PayOS:** [https://payos.vn/docs/](https://payos.vn/docs/) — Luồng thanh toán VietQR tự động 20.000đ trọn đời.

## 1. Triết Lý Thiết Kế Cốt Lõi
1. **Zero-Chrome & Hairlines:** Thẻ tính năng, bảng giá và bảng dữ liệu được tạo thành từ bề mặt phẳng (Flat surfaces) và viền hairline siêu mảnh `1px solid rgba(255, 255, 255, 0.12)` (trên nền tối) hoặc `1px solid rgba(0, 0, 0, 0.08)` (trên nền sáng). Không dùng box-shadow mờ mịt làm bẩn giao diện.
2. **Nhịp điệu Canvas Luân Phiên (Alternating Canvas Rhythm):**
   - **Hero Tile:** Nền đen Obsidian (`#000000`), điểm sáng xanh Sapphire.
   - **Display Showcase (`#xdr-display`):** Chuyển nhịp sang Canvas Parchment (`#f5f5f7`) / Pearl White (`#ffffff`) với chữ Near-Black Ink (`#1d1d1f`) để tạo trải nghiệm triển lãm sống động.
   - **Spotlight Tile (`#pro-spotlight`):** Trở về Space Black (`#000000`) với dải ánh sáng xanh beam và bảng thông số kỹ thuật tối giản.
   - **Simulator & Pricing:** Trình diễn phần cứng và gói bản quyền 20.000đ trong sự tinh tế, tập trung.
3. **Nút Con Nhộng Chuẩn (Pill CTA):** Toàn bộ nút chính và phụ đều dùng hình dáng con nhộng (`border-radius: 9999px`), chiều cao bấm tối thiểu `44px`, chữ rõ ràng.
4. **Quy chuẩn Font Calibri:** Body text chuẩn 10-12pt (`11pt`), hiển thị sắc nét tiếng Việt trên mọi hệ điều hành.
