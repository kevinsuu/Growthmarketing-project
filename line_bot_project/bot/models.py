import matplotlib
matplotlib.use('Agg')  # 必須在導入 pyplot 之前設置
import io
import base64
import pandas as pd
import numpy as np
from django.db import models
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Microsoft YaHei', 'SimHei', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False  
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

class UserTag(models.Model):
    user_id = models.CharField(max_length=50)
    tag_name = models.CharField(max_length=100)
    tagged_at = models.DateTimeField(auto_now_add=True)
    extra_data = models.JSONField(default=dict, blank=True)  # 新增欄位

    class Meta:
        db_table = 'user_tags'
        
    def __str__(self):
        return f"{self.user_id} - {self.tag_name}"
    
    @classmethod
    def get_daily_tag_stats(cls):
        """獲取每日標籤統計數據"""
        try:
            tags = cls.objects.all()
            df = pd.DataFrame(list(tags.values('user_id', 'tag_name', 'tagged_at', 'extra_data')))
            
            if df.empty:
                return [], None
                
            # 轉換時間為日期
            df['date'] = df['tagged_at'].dt.date
            df['status'] = df['extra_data'].apply(lambda x: x.get('status', '-') if x else '-')

            # 統計每個用戶每天的標籤數量
            daily_stats = df.groupby(['date', 'user_id', 'tag_name', 'status']).size().reset_index(name='tag_count')

            
            # 生成圖表
            plt.figure(figsize=(8, 4))  # 縮小圖表尺寸
            
            # 為不同標籤類型設置不同顏色
            tag_types = daily_stats['tag_name'].unique()
            colors = plt.cm.get_cmap('Set3')(np.linspace(0, 1, len(tag_types)))
            
            # 計算每個標籤類型的位置偏移
            bar_width = 0.25  # 設定條形寬度
            x = np.arange(len(df['date'].unique()))  # 創建x軸位置
            
            for i, tag_type in enumerate(tag_types):
                tag_data = daily_stats[daily_stats['tag_name'] == tag_type]
                # 計算偏移位置
                offset = i * bar_width - (len(tag_types) - 1) * bar_width / 2
                
                plt.bar(x + offset,  # x 軸位置加上偏移
                    tag_data['tag_count'], 
                    bar_width,  # 設定寬度
                    label=f'Tag: {tag_type}',
                    color=colors[i],
                    alpha=0.7)
            
            # 設定 x 軸刻度和標籤
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Tag Count', fontsize=12)
            
            # 設定 x 軸刻度位置和標籤
            plt.xticks(x, df['date'].unique(), rotation=45)
            
            # 添加圖例
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
            
            # 調整布局
            plt.tight_layout()
            
            # 將圖表轉換為 base64 字串
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            plt.close()
            
            graph = base64.b64encode(image_png).decode('utf-8')
            
            stats_dict = daily_stats.to_dict('records')
            for stat in stats_dict:
                stat['extra_data'] = {'status': stat.pop('status')}
                
            return stats_dict, graph
            
        except Exception as e:
            print(f"Error generating stats: {str(e)}")
            return [], None

    @classmethod
    def update_message_status(cls, tracking_id, new_status):
        """更新訊息狀態"""
        try:
            logger.info(f"tracking_id: {tracking_id}")
            message = cls.objects.get(
                user_id='narrowcast_message',
                tag_name=f'message_sent_{tracking_id}',
                extra_data__status='send'
            )
            logger.info(f"message: {message}")

            message.extra_data['status'] = new_status
            message.save()
            return True
        except cls.DoesNotExist:
            return False