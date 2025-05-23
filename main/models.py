from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.utils import timezone
import datetime
from django.forms.models import model_to_dict
from rest_framework import serializers

def validate_pdf_size(value):
    limit = 100 * 1024 * 1024
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 100 MiB.')


def validate_image_size(value):
    limit = 1 * 1024 * 1024
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 1 MiB.')


# Create your models here.


class Event(models.Model):
    identifier = models.CharField(max_length=64, unique=True, help_text="Unique Identifier for events")
    title = models.CharField(max_length=255)
    event_image = models.ImageField(upload_to='event_images/', null=True, blank=True, validators=[validate_image_size])
    description = models.TextField( blank=True, null=True)
    # description = RichTextField(blank=True, null=True)
    # description = MarkdownField(rendered_field='rendered', validator=VALIDATOR_STANDARD)
    # rendered = RenderedMarkdownField()

    # Choices of status
    STATUS = (
        ('DRAFT', 'Draft'),
        ('FINAL', 'Final'),
    )
    # Choices of event type
    TYPE = (
        ('ONLINE', 'Online'),
        ('WORKSHOP', 'Workshop'),
        ('TALK', 'Talk Show'),
        ('OFFLINE', 'Other Offline'),
    )

    event_type = models.CharField(max_length=64, choices=TYPE)
    venue = models.CharField(max_length=255, blank=True, null=True, help_text="Venue for Offline Events.")
    url = models.URLField(max_length=255, blank=True, null=True, help_text="URL for Online Events.")
    event_timing = models.DateTimeField(blank=True, null=True)
    facebook_link = models.URLField(null=True, blank=True)
    pub_date = models.DateTimeField(auto_now=True)
    pub_by = models.CharField(max_length=255, blank=True, null=True)
    edited_by = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=64, choices=STATUS)
    show = models.BooleanField(default=True)
    add_to_timeline = models.BooleanField(default=False, help_text="To add to timeline.")
    featured = models.BooleanField(default=False)
    upcoming = models.BooleanField(default=True)

    def __str__(self):
        return self.identifier

    def save(self, *args, **kwargs):
        # Check if Set to 'DRAFT' then set show to false
        # Check online/offline and set url or venue accordingly
        # Offline events may have links for other purpose
        if self.status == "DRAFT":
            self.show = False

        if self.event_type == "ONLINE":
            self.venue = None
        super().save(*args, **kwargs)

        if (self.add_to_timeline == True):
            if not Timeline.objects.filter(event_name=self.title).exists():
                Timeline.objects.create(event_name=self.title, detail=self.description, event_time=self.event_timing.date())

    bts_description = models.TextField(blank=True, null=True, help_text="Behind The Scenes description")
    bts_image = models.ImageField(
        upload_to='event_bts_images/',
        null=True,
        blank=True,
        validators=[validate_image_size],
        help_text="Behind The Scenes image"
    )
    bts_video = models.FileField(
        upload_to='event_bts_videos/',
        null=True,
        blank=True,
        validators=[validate_pdf_size],  # Reusing your file size validator
        help_text="Behind The Scenes video file"
    )
    bts_uploaded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.identifier

    def save(self, *args, **kwargs):
        if self.status == "DRAFT":
            self.show = False

        if self.event_type == "ONLINE":
            self.venue = None
            
        # Update BTS timestamp if any BTS content is added/modified
        if (self.bts_description or self.bts_image or self.bts_video) and not self.bts_uploaded_at:
            self.bts_uploaded_at = timezone.now()
            
        super().save(*args, **kwargs)

        if self.add_to_timeline and not Timeline.objects.filter(event_name=self.title).exists():
            Timeline.objects.create(
                event_name=self.title, 
                detail=self.description, 
                event_time=self.event_timing.date()
            )

def year_choices():
    cuur_year = datetime.date.today().year
    return [(y, y) for y in range(cuur_year, cuur_year + 4 + 1)]

class Facad(models.Model):
    """Faculty Advisor model"""
    post = models.CharField(max_length=100)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    linkedin_link = models.URLField(max_length=200, blank=True, null=True)
    email = models.EmailField(max_length=254)
    image = models.ImageField(upload_to='facad_images/', blank=True, null=True, validators=[validate_image_size])

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.post}"

    class Meta:
        verbose_name = "Faculty Advisor"
        verbose_name_plural = "Faculty Advisors"

class Alumni(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    # Choices of degree
    DEGREE = (
        ('BTECH', 'B.Tech'),
        ('MCA', 'MCA'),
        ('MTECH', 'M.Tech'),
    )

    alias = models.CharField(max_length=64, blank=True, null=True)
    bio = models.TextField(max_length=512, blank=True, null=True)
    image = models.ImageField(upload_to='alumni_images/', blank=True, null=True, validators=[validate_image_size])
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=14, blank=True, null=True)
    degree_name = models.CharField(max_length=64, choices=DEGREE)
    passout_year = models.IntegerField(default=2018)
    position = models.CharField(max_length=255, blank=True, null=True)

    git_link = models.URLField(null=True, blank=True)
    facebook_link = models.URLField(null=True, blank=True)
    twitter_link = models.URLField(null=True, blank=True)
    reddit_link = models.URLField(null=True, blank=True)
    linkedin_link = models.URLField(null=True, blank=True)

    def __str__(self):
        return (self.first_name + " " + self.last_name)

    class Meta:
        verbose_name_plural = "Alumni"



class Profile(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Choices of degree
    DEGREE = (
        ('BTECH', 'B.Tech'),
        ('MCA', 'MCA'),
        ('MTECH', 'M.Tech'),
    )

    YEAR = (
        ('1', 'First'),
        ('2', 'Second'),
        ('3', 'Third'),
        ('4', 'Final'),
    )

    alias = models.CharField(max_length=64, blank=True, null=True)
    bio = models.TextField(max_length=512, blank=True, null=True)
    image = models.ImageField(upload_to='member_images/', blank=True, null=True, validators=[validate_image_size])
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=14, blank=True, null=True)
    degree_name = models.CharField(max_length=64, choices=DEGREE)
    passout_year = models.IntegerField(choices=year_choices(), default=2018)
    position = models.CharField(max_length=255, blank=True, null=True)
    convert_to_alumni = models.BooleanField(default=False)

    git_link = models.URLField(null=True, blank=True)
    facebook_link = models.URLField(null=True, blank=True)
    twitter_link = models.URLField(null=True, blank=True)
    reddit_link = models.URLField(null=True, blank=True)
    linkedin_link = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.first_name
    
    def save(self, *args, **kwargs):
        """
        Checks if the profile belongs to an alumni or not and converts to alumni if True
        """
        if self.convert_to_alumni == True:
                class AlumniSerializer(serializers.ModelSerializer):
                    class Meta:
                     model = Alumni
                     fields = '__all__'

                # Converting the Profile instance to Alumni instance
                alumni_data = AlumniSerializer(self).data

                # Creating a new Alumni instance from the serialized data
                alumni_serializer = AlumniSerializer(data=alumni_data)
                alumni_serializer.is_valid(raise_exception=True)
                alumni_serializer.save()

                # Deleting the Profile instance after converting it to Alumni
                self.delete()
                return
        else: 
            super(Profile, self).save(*args, **kwargs)




class CarouselImage(models.Model):
    identifier = models.CharField(max_length=64, unique=True)
    image = models.ImageField(upload_to='card_images/', validators=[validate_image_size])
    mobile_image = models.ImageField(upload_to='card_images/mobile/',
                                     validators=[validate_image_size],
                                     blank=True,
                                     null=True)
    heading = models.CharField(max_length=255, blank=True, null=True)
    sub_heading = models.TextField(max_length=1024, blank=True, null=True)

    def __str__(self):
        return self.identifier


class About(models.Model):
    identifier = models.CharField(max_length=64, unique=True)
    # remove blank and null after test
    heading = models.CharField(max_length=255, blank=True, null=True)
    content = RichTextField(blank=True, null=True)
    # content = MarkdownField(rendered_field='rendered', validator=VALIDATOR_STANDARD)
    # rendered = RenderedMarkdownField()

    def __str__(self):
        return self.identifier


from django.db import models
from django.core.exceptions import ValidationError

def validate_image_size(value):
    """Validate that uploaded image is <= 2MB"""
    limit = 2 * 1024 * 1024  # 2MB
    if value.size > limit:
        raise ValidationError('Image too large. Size should not exceed 2MB.')

class Project(models.Model):
    identifier = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True, null=True)
    gitlink = models.URLField(null=True, blank=True)
    
    # Added image field matching TechBytes style
    image = models.ImageField(
        upload_to='project_images/%Y/%m/%d/',  # Organizes by date
        null=True,
        blank=True,
        validators=[validate_image_size],
        help_text='Upload project image (max 2MB)'
    )

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        """Delete image file when project is deleted"""
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)


class Contact(models.Model):
    """For Contact Us endpoint only"""
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=14, blank=True, null=True)
    message = models.TextField(max_length=1024, blank=True, null=True)


class Activity(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=1024, blank=True, null=True)
    image = models.ImageField(upload_to='activity_images/', blank=True, null=True, validators=[validate_image_size])

    class Meta:
        verbose_name_plural = "Activities"

    def __str__(self):
        return self.title


class Linit(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=1024, blank=True, null=True)
    image = models.ImageField(upload_to='linit_images/', blank=True, null=True)
    year_edition = models.IntegerField(default=2018)

    def __str__(self):
        return self.title

class LinitImage(models.Model):
    linit_year = models.ForeignKey(Linit, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='linit_magzine_images/', blank=True, null=True)


class SpecialToken(models.Model):
    """This is intended for special use cases,
        where a feature needs to be an
        'members only' feature"""

    name = models.CharField(max_length=255)
    value = models.CharField(max_length=16)
    used = models.SmallIntegerField(default=0)
    max_usage = models.IntegerField(default=1)
    valid_till = models.DateTimeField()

    def is_valid(self):
        t_now = timezone.now()
        if self.used < self.max_usage and t_now < self.valid_till:
            return True
        return False

    def set_valid_default(self):
        return datetime.datetime.now() + datetime.timedelta(hours=6)

    def save(self, *args, **kwargs):
        if not self.value:
            self.value = get_random_string(16)
        return super(SpecialToken, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class Timeline(models.Model):
    event_name = models.CharField(max_length=120)
    detail = models.TextField(blank=True, null=True)
    event_time = models.DateField(blank=True, auto_now_add=False)

    def __str__(self):
        return self.event_name

    # def save(self, *args, **kwargs):
    #     if not self.id:
    #         self.event_time = timezone.now()
    #     return super(Timeline, self).save(*args, **kwargs)

class TechBytes(models.Model):
    title = models.CharField(max_length=128)
    image = models.ImageField(upload_to='tb_images/', null=True, blank=True, validators=[validate_image_size])
    body = models.TextField(blank=True, null=True)
    link = models.URLField(max_length=255, blank=True, null=True, help_text="Optional external link for the post")
    pub_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "TechBytes Posts"


class DevPost(models.Model):
    title = models.CharField(max_length=128)
    image = models.ImageField(upload_to='dev_images/', null=True, blank=True, validators=[validate_image_size])
    dev_link = models.URLField(blank=False)
    body = RichTextField(blank=True, null=True)
    # body = MarkdownField(rendered_field='rendered', validator=VALIDATOR_STANDARD)
    # rendered = RenderedMarkdownField()
    pub_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Config(models.Model):
    key = models.CharField(max_length=64, unique=True)
    value = models.CharField(max_length=1024)
    enable = models.BooleanField(default=True)

    def __str__(self):
        return self.key


class Sponsor(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='sponsors/', validators=[validate_image_size])
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name
    
class CTF(models.Model):
    name = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='ctf/', validators=[validate_image_size])
    link = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name