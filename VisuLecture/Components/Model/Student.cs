namespace VisuLecture.Components.Model;

public class Student
{
    public Student(string id, string firstName, string lastName, int age, int lunette, int theme, string remarque)
    {
        Id = id;
        FirstName = firstName;
        LastName = lastName;
        Age = age;
        Lunette = lunette;
        Theme = theme;
        Remarque = remarque;
    }

    public Student()
    {
        Id = Guid.NewGuid().ToString("N");
        FirstName = "";
        LastName = "";
        Age = 0;
        Lunette = 1;
        Theme = 1;
        Remarque = "";
    }

    public string Id { get; set; }
    public string FirstName { get; set; } = "";
    public string LastName { get; set; } = "";
    public int Age { get; set; }
    public int Lunette { get; set; }
    public int Theme { get; set; }
    public string Remarque { get; set; } = "";
    
    // Collection de lectures (enregistrements)
    public ICollection<Reading> Readings { get; set; } = new List<Reading>();

    public void UpdateFrom(Student stu)
    {
        FirstName = stu.FirstName;
        LastName = stu.LastName;
        Age = stu.Age;
        Lunette = stu.Lunette;
        Theme = stu.Theme;
        Remarque = stu.Remarque;
    }
}