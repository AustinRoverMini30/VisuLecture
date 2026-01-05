using Microsoft.EntityFrameworkCore;
using VisuLecture.Components.Model;

namespace VisuLecture.Components.Controller;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options)
        : base(options) { }

    public DbSet<Student> Students => Set<Student>();
    public DbSet<TextRecord> TextRecords => Set<TextRecord>();
    public DbSet<Reading> Readings => Set<Reading>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Configuration de la relation Student -> Readings
        modelBuilder.Entity<Reading>()
            .HasOne(r => r.Student)
            .WithMany(s => s.Readings)
            .HasForeignKey(r => r.StudentId)
            .OnDelete(DeleteBehavior.Cascade);

        // Configuration de la relation TextRecord -> Readings
        modelBuilder.Entity<Reading>()
            .HasOne(r => r.TextRecord)
            .WithMany()
            .HasForeignKey(r => r.TextId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}