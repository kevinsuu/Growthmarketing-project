from django.db import models

class UserTag(models.Model):
    user_id = models.CharField(max_length=50)
    tag_name = models.CharField(max_length=100)
    tagged_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_tags'
        
    def __str__(self):
        return f"{self.user_id} - {self.tag_name}"