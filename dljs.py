import pandas as pd
from datetime import datetime, time
import streamlit as st

# 设置页面配置
st.set_page_config(
    page_title="电费计算器",
    page_icon="⚡",
    layout="centered",  # 改为 centered 布局
    initial_sidebar_state="collapsed"  # 默认收起侧边栏
)

# 添加移动端优化的 CSS
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 5px;
        padding-right: 5px;
    }
    
    /* 移动端适配 */
    @media (max-width: 768px) {
        .stButton>button {
            width: 100%;
            margin: 0.5rem 0;
        }
        .stNumberInput>div>div>input {
            font-size: 16px !important;
            padding: 0.5rem !important;
        }
        .stSelectbox>div>div>div {
            font-size: 16px !important;
        }
        h1 {
            font-size: 1.5rem !important;
        }
        h2 {
            font-size: 1.3rem !important;
        }
        h3 {
            font-size: 1.1rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

class ElectricityBillCalculator:
    """
    电费计算器类
    """
    def __init__(self):
        """
        初始化电价表和时段划分
        """
        # 初始化电价表
        self.single_rate_table = self._init_single_rate_table()
        self.double_rate_table = self._init_double_rate_table()
        
        # 初始化需量电价表
        self.demand_prices = {
            "1-10千伏": 40,
            "35-110千伏以下": 36.9,
            "110千伏": 33.7,
            "220千伏及以上": 30.5
        }
        
        # 初始化容量电价表
        self.capacity_prices = {
            "1-10千伏": 25,
            "35-110千伏以下": 23,
            "110千伏": 21,
            "220千伏及以上": 19
        }

    def _init_single_rate_table(self):
        """
        初始化单一制电价表
        """
        # 这里可以从Excel文件导入或直接定义
        return {
            #1月数据
            ("不满1千伏", 1): {"base": 0.712570375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("1-10千伏", 1): {"base": 0.685070375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("35-110千伏", 1): {"base":0.658270375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("110千伏及以上", 1): {"base": 0.63157037, "low": 0.45, "high": 1.72, "peak": 2.064},
            #2月数据 
            ("不满1千伏", 2): {"base": 0.721953375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("1-10千伏", 2): {"base": 0.694453375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("35-110千伏", 2): {"base":0.667653375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("110千伏及以上", 2): {"base":0.640953375, "low": 0.45, "high": 1.72, "peak": 2.064},
            #3月数据
            ("不满1千伏", 3): {"base": 0.742258375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("1-10千伏", 3): {"base": 0.714758375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("35-110千伏", 3): {"base":0.687958375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("110千伏及以上", 3): {"base":0.661258375, "low": 0.45, "high": 1.72, "peak": 2.064},
        }

    def _init_double_rate_table(self):
        """
        初始化两部制电价表
        """
        return {
            # 1月数据
            ("1-10千伏", 1): {"base": 0.685070375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("35-110千伏以下", 1): {"base": 0.662670375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("110千伏", 1): {"base": 0.638070375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("220千伏及以上", 1): {"base": 0.620070375, "low": 0.45, "high": 1.72, "peak": 2.064},
            
            # 2月数据
            ("1-10千伏", 2): {"base": 0.694453375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("35-110千伏以下", 2): {"base": 0.672053375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("110千伏", 2): {"base": 0.647453375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("220千伏及以上", 2): {"base": 0.629453375, "low": 0.45, "high": 1.72, "peak": 2.064},
            
            # 3月数据
            ("1-10千伏", 3): {"base": 0.714758375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("35-110千伏以下", 3): {"base": 0.692358375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("110千伏", 3): {"base": 0.667758375, "low": 0.45, "high": 1.72, "peak": 2.064},
            ("220千伏及以上", 3): {"base": 0.649758375, "low": 0.45, "high": 1.72, "peak": 2.064}
        }

    def _get_time_period(self, month: int, hour: int) -> str:
        """
        根据月份和小时确定时段类型
        
        @param month: 月份
        @param hour: 小时
        @return: 时段类型（低谷/平段/高峰/尖峰）
        """
        # 1月、12月的时段划分
        if month in [1, 12]:
            if 0 <= hour < 7:  # 0:00-7:00
                return "low"
            elif 7 <= hour < 16:  # 7:00-16:00
                return "base"
            elif 17 <= hour < 19:  # 17:00-19:00
                return "peak"
            else:  # 16:00-17:00, 19:00-24:00
                return "high"
        
        # 2月、6月的时段划分
        elif month in [2, 6]:
            if 0 <= hour < 7:  # 0:00-7:00
                return "low"
            elif 7 <= hour < 16:  # 7:00-16:00
                return "base"
            else:  # 16:00-24:00
                return "high"
        
        # 3月、4月、5月、9月、10月、11月的时段划分
        elif month in [3, 4, 5, 9, 10, 11]:
            if (0 <= hour < 6) or (11 <= hour < 14):  # 0:00-6:00, 11:00-14:00
                return "low"
            elif (6 <= hour < 11) or (14 <= hour < 16):  # 6:00-11:00, 14:00-16:00
                return "base"
            else:  # 16:00-24:00
                return "high"
        
        # 7月、8月的时段划分
        elif month in [7, 8]:
            if 0 <= hour < 7:  # 0:00-7:00
                return "low"
            elif 7 <= hour < 16:  # 7:00-16:00
                return "base"
            elif 20 <= hour < 23:  # 20:00-23:00
                return "peak"
            else:  # 16:00-20:00, 23:00-24:00
                return "high"
        
        # 默认返回平段（不应该到达这里）
        return "base"

    def calculate_electricity_fee(self, 
                                transformer_capacity: float,
                                voltage_level: str,
                                month: int,
                                daily_usage: dict,
                                rate_type: str,
                                days_in_month: int = 30) -> dict:
        """
        计算电费
        
        @param transformer_capacity: 变压器容量(kVA)
        @param voltage_level: 电压等级
        @param month: 月份
        @param daily_usage: 每小时用电量字典
        @param rate_type: 计费类型（单一制/两部制）
        @param days_in_month: 每月用电天数
        @return: 电费计算结果
        """
        # 计算各时段用电量
        period_usage = {"low": 0, "base": 0, "high": 0, "peak": 0}
        for hour, usage in daily_usage.items():
            period = self._get_time_period(month, hour)
            period_usage[period] += usage * days_in_month  # 使用实际用电天数
            
        # 获取电价表
        rate_table = self.single_rate_table if rate_type == "单一制" else self.double_rate_table
        rates = rate_table.get((voltage_level, month))
        
        # 计算电度电费
        energy_fee = (
            period_usage["low"] * rates["base"] * rates["low"] +
            period_usage["base"] * rates["base"] +
            period_usage["high"] * rates["base"] * rates["high"] +
            period_usage["peak"] * rates["base"] * rates["peak"]
        )
        
        result = {"energy_fee": energy_fee}
        
        # 如果是两部制，计算容量电费
        if rate_type == "两部制":
            # 计算变压器利用率
            total_usage = sum(period_usage.values())
            utilization_rate = total_usage / (transformer_capacity * 24 * days_in_month)
            
            if utilization_rate >= 0.7:
                # 使用容量电价
                capacity_fee = transformer_capacity * self.capacity_prices[voltage_level]
                result["capacity_fee"] = capacity_fee
                result["fee_type"] = "容量电费"
            else:
                # 使用需量电价
                contract_demand = transformer_capacity * 0.4 * 0.9
                demand_fee = contract_demand * self.demand_prices[voltage_level]
                result["capacity_fee"] = demand_fee
                result["fee_type"] = "需量电费"
            
            result["total_fee"] = result["energy_fee"] + result["capacity_fee"]
        else:
            result["total_fee"] = result["energy_fee"]
            
        return result

def create_streamlit_app():
    """
    创建Streamlit Web应用界面
    """
    st.title("河南省2025年代理购电电费计算器")
    
    # 用户输入
    transformer_capacity = st.number_input("变压器容量(kVA)", min_value=0.0)
    voltage_level = st.selectbox("电压等级", 
                                ["不满1千伏", "1-10千伏", "35-110千伏以下", 
                                 "110千伏", "220千伏及以上"])
    month = st.selectbox("月份", range(1, 13))
    
    # 添加每月用电天数选项
    days_in_month = st.number_input("每月用电天数", min_value=1, max_value=31, value=30)
    
    rate_type = st.radio("计费类型", ["单一制", "两部制"])
    
    # 每小时用电量输入
    st.subheader("日用电量（千瓦时）")
    
    # 添加批量输入功能
    col1, col2 = st.columns(2)
    with col1:
        batch_input = st.checkbox("启用批量输入")
    
    daily_usage = {}
    
    if batch_input:
        with col2:
            pattern_type = st.selectbox("选择用电模式", 
                                      ["工作日模式", "均匀分布", "自定义"])
        
        if pattern_type == "工作日模式":
            # 工作时间用电量（8:00-18:00）
            work_hours_usage = st.number_input("工作时间用电量 (8:00-18:00)", 
                                             min_value=0.0, format="%f")
            # 非工作时间用电量
            non_work_hours_usage = st.number_input("非工作时间用电量", 
                                                min_value=0.0, format="%f")
            
            # 填充每小时用电量
            for hour in range(24):
                if 8 <= hour < 18:
                    daily_usage[hour] = work_hours_usage / 10  # 平均分配到工作时间
                else:
                    daily_usage[hour] = non_work_hours_usage / 14  # 平均分配到非工作时间
                    
        elif pattern_type == "均匀分布":
            # 总日用电量
            total_daily_usage = st.number_input("总日用电量", 
                                             min_value=0.0, format="%f")
            
            # 均匀分配到24小时
            for hour in range(24):
                daily_usage[hour] = total_daily_usage / 24
                
        else:  # 自定义
            # 根据月份显示不同的时段输入选项
            st.write("请根据所选月份输入各时段用电量：")
            
            if month in [1, 12]:  # 1月和12月
                low_hours_usage = st.number_input("低谷时段用电量 (0:00-7:00)", 
                                              min_value=0.0, format="%f")
                base_hours_usage = st.number_input("平段时段用电量 (7:00-16:00)", 
                                               min_value=0.0, format="%f")
                peak_hours_usage = st.number_input("尖峰时段用电量 (17:00-19:00)", 
                                               min_value=0.0, format="%f")
                high_hours_usage = st.number_input("高峰时段用电量 (16:00-17:00, 19:00-24:00)", 
                                               min_value=0.0, format="%f")
                
                # 填充每小时用电量
                for hour in range(24):
                    if 0 <= hour < 7:
                        daily_usage[hour] = low_hours_usage / 7
                    elif 7 <= hour < 16:
                        daily_usage[hour] = base_hours_usage / 9
                    elif 17 <= hour < 19:
                        daily_usage[hour] = peak_hours_usage / 2
                    else:  # 16:00-17:00, 19:00-24:00
                        daily_usage[hour] = high_hours_usage / 6
                
            elif month in [2, 6]:  # 2月和6月
                low_hours_usage = st.number_input("低谷时段用电量 (0:00-7:00)", 
                                              min_value=0.0, format="%f")
                base_hours_usage = st.number_input("平段时段用电量 (7:00-16:00)", 
                                               min_value=0.0, format="%f")
                high_hours_usage = st.number_input("高峰时段用电量 (16:00-24:00)", 
                                               min_value=0.0, format="%f")
                
                # 填充每小时用电量
                for hour in range(24):
                    if 0 <= hour < 7:
                        daily_usage[hour] = low_hours_usage / 7
                    elif 7 <= hour < 16:
                        daily_usage[hour] = base_hours_usage / 9
                    else:  # 16:00-24:00
                        daily_usage[hour] = high_hours_usage / 8
                
            elif month in [3, 4, 5, 9, 10, 11]:  # 3-5月和9-11月
                low_hours_usage = st.number_input("低谷时段用电量 (0:00-6:00, 11:00-14:00)", 
                                              min_value=0.0, format="%f")
                base_hours_usage = st.number_input("平段时段用电量 (6:00-11:00, 14:00-16:00)", 
                                               min_value=0.0, format="%f")
                high_hours_usage = st.number_input("高峰时段用电量 (16:00-24:00)", 
                                               min_value=0.0, format="%f")
                
                # 填充每小时用电量
                for hour in range(24):
                    if (0 <= hour < 6) or (11 <= hour < 14):
                        daily_usage[hour] = low_hours_usage / 9  # 总共9小时
                    elif (6 <= hour < 11) or (14 <= hour < 16):
                        daily_usage[hour] = base_hours_usage / 7  # 总共7小时
                    else:  # 16:00-24:00
                        daily_usage[hour] = high_hours_usage / 8  # 总共8小时
                
            elif month in [7, 8]:  # 7月和8月
                low_hours_usage = st.number_input("低谷时段用电量 (0:00-7:00)", 
                                              min_value=0.0, format="%f")
                base_hours_usage = st.number_input("平段时段用电量 (7:00-16:00)", 
                                               min_value=0.0, format="%f")
                peak_hours_usage = st.number_input("尖峰时段用电量 (20:00-23:00)", 
                                               min_value=0.0, format="%f")
                high_hours_usage = st.number_input("高峰时段用电量 (16:00-20:00, 23:00-24:00)", 
                                               min_value=0.0, format="%f")
                
                # 填充每小时用电量
                for hour in range(24):
                    if 0 <= hour < 7:
                        daily_usage[hour] = low_hours_usage / 7
                    elif 7 <= hour < 16:
                        daily_usage[hour] = base_hours_usage / 9
                    elif 20 <= hour < 23:
                        daily_usage[hour] = peak_hours_usage / 3
                    else:  # 16:00-20:00, 23:00-24:00
                        daily_usage[hour] = high_hours_usage / 5
        
        # 显示生成的每小时用电量
        st.subheader("生成的每小时用电量")
        hour_cols = st.columns(6)
        for i, hour in enumerate(range(24)):
            with hour_cols[i % 6]:
                st.text(f"{hour:02d}:00: {daily_usage[hour]:.2f}")
                
    else:
        # 原始的每小时输入方式
        cols = st.columns(6)
        for hour in range(24):
            with cols[hour % 6]:
                daily_usage[hour] = st.number_input(f"{hour:02d}:00", 
                                                  min_value=0.0, 
                                                  format="%f")
    
    if st.button("计算电费"):
        calculator = ElectricityBillCalculator()
        
        # 修改计算函数调用，传入用电天数
        result = calculator.calculate_electricity_fee(
            transformer_capacity,
            voltage_level,
            month,
            daily_usage,
            rate_type,
            days_in_month  # 添加用电天数参数
        )
        
        st.subheader("计算结果")
        st.write(f"电度电费: {result['energy_fee']:.2f} 元")
        if rate_type == "两部制":
            st.write(f"{result['fee_type']}: {result['capacity_fee']:.2f} 元")
        st.write(f"总电费: {result['total_fee']:.2f} 元")

if __name__ == "__main__":
    create_streamlit_app() 