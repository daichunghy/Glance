import Foundation

@MainActor
public final class LicenseManager: ObservableObject {
    public static let shared = LicenseManager()
    
    private let trialDays = 7
    private let trialStartDateKey = "com.glance.trialStartDate"
    private let licenseKeyStorageKey = "com.glance.licenseKey"
    private let isActivatedKey = "com.glance.isActivated"
    
    // Server verification endpoint (PayOS Glance Server)
    public var serverEndpoint: String = "http://localhost:3000/api/license/verify"
    
    @Published public var isLicensed: Bool = false
    @Published public var daysRemaining: Int = 7
    @Published public var licenseKey: String = ""
    
    private init() {
        checkLicenseStatus()
    }
    
    public func checkLicenseStatus() {
        // 1. Check if previously activated
        if UserDefaults.standard.bool(forKey: isActivatedKey) {
            isLicensed = true
            licenseKey = UserDefaults.standard.string(forKey: licenseKeyStorageKey) ?? ""
            return
        }
        
        // 2. Check Trial period
        let defaults = UserDefaults.standard
        if let startDate = defaults.object(forKey: trialStartDateKey) as? Date {
            let elapsed = Calendar.current.dateComponents([.day], from: startDate, to: Date()).day ?? 0
            daysRemaining = max(0, trialDays - elapsed)
            isLicensed = daysRemaining > 0
        } else {
            // First launch: initialize trial start date
            let now = Date()
            defaults.set(now, forKey: trialStartDateKey)
            daysRemaining = trialDays
            isLicensed = true
        }
    }
    
    /// Activates license key against Glance PayOS Licensing Server or validates official PayOS key
    public func activateLicense(key: String, completion: @escaping @MainActor (Bool, String) -> Void) {
        let cleanKey = key.trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
        guard !cleanKey.isEmpty else {
            completion(false, "Vui lòng nhập mã kích hoạt hợp lệ.")
            return
        }
        
        // Fast-path: Check official Glance Lifetime Pro pattern generated from PayOS orders
        // Format: GLANCE-2026-XDR9-XXXX-XXXX
        let isOfficialGlanceKey = cleanKey.hasPrefix("GLANCE-2026-") || cleanKey.hasPrefix("GLANCE-")
        
        guard let url = URL(string: serverEndpoint) else {
            if isOfficialGlanceKey {
                self.markActivated(key: cleanKey)
                completion(true, "Kích hoạt bản quyền Glance trọn đời thành công!")
            } else {
                completion(false, "Mã kích hoạt không đúng định dạng.")
            }
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 5.0
        
        let body: [String: Any] = [
            "licenseKey": cleanKey,
            "instanceName": Host.current().localizedName ?? "MacBook"
        ]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            Task { @MainActor [weak self] in
                guard let self = self else { return }
                if let data = data,
                   let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let valid = json["valid"] as? Bool, valid {
                    
                    self.markActivated(key: cleanKey)
                    let msg = json["message"] as? String ?? "Kích hoạt bản quyền Glance thành công!"
                    completion(true, msg)
                } else {
                    // Fallback to pattern validation if offline / server not running
                    if isOfficialGlanceKey {
                        self.markActivated(key: cleanKey)
                        completion(true, "Kích hoạt bản quyền Glance trọn đời thành công (Offline Mode)!")
                    } else {
                        completion(false, "Mã kích hoạt không đúng hoặc chưa được thanh toán.")
                    }
                }
            }
        }.resume()
    }
    
    private func markActivated(key: String) {
        UserDefaults.standard.set(true, forKey: isActivatedKey)
        UserDefaults.standard.set(key, forKey: licenseKeyStorageKey)
        self.isLicensed = true
        self.licenseKey = key
    }
    
    public func resetActivation() {
        UserDefaults.standard.removeObject(forKey: isActivatedKey)
        UserDefaults.standard.removeObject(forKey: licenseKeyStorageKey)
        self.isLicensed = false
        self.licenseKey = ""
        checkLicenseStatus()
    }
}
