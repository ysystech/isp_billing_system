from django.contrib import admin
from .models import LCP, Splitter, NAP


class SplitterInline(admin.TabularInline):
    model = Splitter
    extra = 0
    fields = ['code', 'type', 'location', 'is_active']
    readonly_fields = ['port_capacity', 'used_ports', 'available_ports']
    
    def port_capacity(self, obj):
        return obj.port_capacity
    
    def used_ports(self, obj):
        return obj.used_ports
    
    def available_ports(self, obj):
        return obj.available_ports


class NAPInline(admin.TabularInline):
    model = NAP
    extra = 0
    fields = ['code', 'name', 'splitter_port', 'location', 'port_capacity', 'is_active']


@admin.register(LCP)
class LCPAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'barangay', 'coordinates_display', 'splitter_count', 'nap_count', 'is_active']
    list_filter = ['is_active', 'barangay']
    search_fields = ['code', 'name', 'location']
    inlines = [SplitterInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'barangay', 'is_active')
        }),
        ('Location Details', {
            'fields': ('location', 'latitude', 'longitude', 'location_accuracy', 'location_notes', 'coverage_radius_meters')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def coordinates_display(self, obj):
        return obj.coordinates_display
    coordinates_display.short_description = 'Coordinates'
    
    def splitter_count(self, obj):
        return obj.splitters.count()
    splitter_count.short_description = 'Splitters'
    
    def nap_count(self, obj):
        return NAP.objects.filter(splitter__lcp=obj).count()
    nap_count.short_description = 'Total NAPs'


@admin.register(Splitter)
class SplitterAdmin(admin.ModelAdmin):
    list_display = ['code', 'lcp', 'type', 'location', 'used_ports', 'available_ports', 'is_active']
    list_filter = ['is_active', 'type', 'lcp']
    search_fields = ['code', 'lcp__code', 'lcp__name']
    inlines = [NAPInline]
    
    def used_ports(self, obj):
        return f"{obj.used_ports}/{obj.port_capacity}"
    used_ports.short_description = 'Port Usage'
    
    def available_ports(self, obj):
        return obj.available_ports
    available_ports.short_description = 'Available'


@admin.register(NAP)
class NAPAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'splitter', 'splitter_port', 'location', 'port_capacity', 'is_active']
    list_filter = ['is_active', 'splitter__lcp', 'port_capacity']
    search_fields = ['code', 'name', 'location', 'splitter__code', 'splitter__lcp__code']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('splitter__lcp')
