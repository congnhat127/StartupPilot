class TaxCalculator:
    """
    Công cụ (Tool) tính Thuế Thu nhập cá nhân (TNCN) Toàn diện theo Luật Thuế TNCN Việt Nam.
    Bao gồm tất cả 10 loại thu nhập chịu thuế.
    """

    # ==========================================
    # NHÓM 1: TIỀN LƯƠNG, TIỀN CÔNG
    # ==========================================
    GIAM_TRU_BAN_THAN = 11_000_000
    GIAM_TRU_NGUOI_PHU_THUOC = 4_400_000

    @staticmethod
    def calculate_personal_income_tax(total_income: float, dependents: int = 0, insurance_deduction: float = 0.0) -> dict:
        """Cá nhân cư trú - Ký HĐLĐ >= 3 tháng (Biểu lũy tiến 7 bậc)"""
        total_deduction = TaxCalculator.GIAM_TRU_BAN_THAN + (dependents * TaxCalculator.GIAM_TRU_NGUOI_PHU_THUOC) + insurance_deduction
        taxable_income = max(0.0, total_income - total_deduction)
        
        tax_amount = 0.0
        if taxable_income <= 5_000_000: tax_amount = taxable_income * 0.05
        elif taxable_income <= 10_000_000: tax_amount = (5_000_000 * 0.05) + ((taxable_income - 5_000_000) * 0.10)
        elif taxable_income <= 18_000_000: tax_amount = 250_000 + 500_000 + ((taxable_income - 10_000_000) * 0.15)
        elif taxable_income <= 32_000_000: tax_amount = 750_000 + 1_200_000 + ((taxable_income - 18_000_000) * 0.20)
        elif taxable_income <= 52_000_000: tax_amount = 1_950_000 + 2_800_000 + ((taxable_income - 32_000_000) * 0.25)
        elif taxable_income <= 80_000_000: tax_amount = 4_750_000 + 5_000_000 + ((taxable_income - 52_000_000) * 0.30)
        else: tax_amount = 9_750_000 + 8_400_000 + ((taxable_income - 80_000_000) * 0.35)
            
        return {"loai_thue": "Tiền lương (Cư trú)", "thu_nhap_tinh_thue": taxable_income, "tien_thue_phai_nop": tax_amount}

    @staticmethod
    def calculate_freelance_tax(total_income: float) -> dict:
        """Cá nhân cư trú - Không HĐLĐ / HĐLĐ < 3 tháng (Khấu trừ 10%)"""
        tax_amount = total_income * 0.10 if total_income >= 2_000_000 else 0.0
        return {"loai_thue": "Lao động tự do (Khấu trừ 10%)", "tien_thue_phai_nop": tax_amount}

    @staticmethod
    def calculate_non_resident_tax(total_income: float) -> dict:
        """Cá nhân không cư trú (Khấu trừ cứng 20%)"""
        return {"loai_thue": "Tiền lương (Không cư trú)", "tien_thue_phai_nop": total_income * 0.20}

    # ==========================================
    # NHÓM 2: KINH DOANH & ĐẦU TƯ
    # ==========================================
    @staticmethod
    def calculate_business_tax(revenue: float, industry_type: str) -> dict:
        """
        Thu nhập từ kinh doanh (Hộ kinh doanh cá thể). Tính riêng thuế TNCN.
        industry_type: 'phan_phoi' (0.5%), 'dich_vu' (2%), 'san_xuat_van_tai' (1.5%), 'khac' (1%)
        """
        rates = {
            'phan_phoi': 0.005,
            'dich_vu': 0.02,
            'san_xuat_van_tai': 0.015,
            'khac': 0.01
        }
        rate = rates.get(industry_type, 0.01)
        # Chỉ tính thuế nếu doanh thu năm > 100 triệu (Giả định đầu vào là doanh thu đã đạt ngưỡng)
        return {"loai_thue": f"Kinh doanh ({industry_type})", "ty_le_tncn": rate, "tien_thue_phai_nop": revenue * rate}

    @staticmethod
    def calculate_capital_investment_tax(dividend_value: float) -> dict:
        """Thu nhập từ đầu tư vốn (Cổ tức) - 5%"""
        return {"loai_thue": "Đầu tư vốn (Cổ tức)", "tien_thue_phai_nop": dividend_value * 0.05}

    @staticmethod
    def calculate_capital_transfer_tax(selling_price: float, purchase_price: float, related_expenses: float = 0) -> dict:
        """Chuyển nhượng phần vốn góp - 20% trên Lợi nhuận"""
        profit = max(0.0, selling_price - purchase_price - related_expenses)
        return {"loai_thue": "Chuyển nhượng vốn góp", "loi_nhuan": profit, "tien_thue_phai_nop": profit * 0.20}

    @staticmethod
    def calculate_securities_transfer_tax(transfer_price: float) -> dict:
        """Chuyển nhượng chứng khoán - 0.1% trên Giá bán"""
        return {"loai_thue": "Chuyển nhượng chứng khoán", "tien_thue_phai_nop": transfer_price * 0.001}

    # ==========================================
    # NHÓM 3: BẤT ĐỘNG SẢN & TÀI SẢN KHÁC
    # ==========================================
    @staticmethod
    def calculate_real_estate_tax(transfer_price: float) -> dict:
        """Chuyển nhượng Bất động sản - 2% trên Giá chuyển nhượng"""
        return {"loai_thue": "Chuyển nhượng Bất động sản", "tien_thue_phai_nop": transfer_price * 0.02}

    @staticmethod
    def calculate_prize_inheritance_gift_tax(asset_value: float) -> dict:
        """Trúng thưởng, Thừa kế, Quà tặng - 10% phần vượt quá 10 triệu"""
        taxable = max(0.0, asset_value - 10_000_000)
        return {"loai_thue": "Trúng thưởng/Thừa kế/Quà tặng", "phan_vuot_muc": taxable, "tien_thue_phai_nop": taxable * 0.10}

    @staticmethod
    def calculate_copyright_franchise_tax(contract_value: float) -> dict:
        """Bản quyền, Nhượng quyền thương mại - 5% phần vượt quá 10 triệu"""
        taxable = max(0.0, contract_value - 10_000_000)
        return {"loai_thue": "Bản quyền/Nhượng quyền", "phan_vuot_muc": taxable, "tien_thue_phai_nop": taxable * 0.05}

# ==========================================
# TEST NHANH
# ==========================================
if __name__ == "__main__":
    print("1. Bán nhà 5 tỷ:")
    print(TaxCalculator.calculate_real_estate_tax(5_000_000_000))
    
    print("\n2. Trúng Vietlott 15 triệu:")
    print(TaxCalculator.calculate_prize_inheritance_gift_tax(15_000_000))
    
    print("\n3. Bán cổ phiếu giá 100 triệu:")
    print(TaxCalculator.calculate_securities_transfer_tax(100_000_000))
